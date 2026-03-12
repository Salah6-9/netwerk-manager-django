import os
import time
import re
import shlex
import subprocess
import logging

from django.db import transaction
from django.utils import timezone

from devices.models import Device
from monitoring.models import ScanLog, ScanRun, SystemConfig

logger = logging.getLogger(__name__)

# ==========================================================
# Lock configuration
# ==========================================================

LOCK_FILE = "/tmp/network_scan.lock"
LOCK_TIMEOUT = 300  # seconds


# ==========================================================
# Regex patterns
# ==========================================================

HOST_RE = re.compile(
    r"^Nmap scan report for\s+(\d+\.\d+\.\d+\.\d+)",
    re.MULTILINE
)

MAC_RE = re.compile(r"MAC Address:\s*([0-9A-Fa-f:]{17})")


# ==========================================================
# Lock helpers
# ==========================================================

def acquire_lock():
    """Create lock file if no active scan is running."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                timestamp = float(f.read().strip())

            # Remove stale lock
            if time.time() - timestamp > LOCK_TIMEOUT:
                logger.warning("Removing stale scan lock.")
                os.remove(LOCK_FILE)
            else:
                return False

        except (ValueError, OSError):
            logger.warning("Removing corrupted scan lock.")
            try:
                os.remove(LOCK_FILE)
            except OSError:
                pass

    with open(LOCK_FILE, "w") as f:
        f.write(str(time.time()))

    return True


def release_lock():
    """Remove lock file safely."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except OSError:
        pass


# ==========================================================
# Nmap execution
# ==========================================================

def run_nmap_scan(network_range, use_sudo=False, timeout=240):
    """Run nmap and return raw output."""
    cmd = f"nmap -sn -PR {shlex.quote(network_range)}"
    if use_sudo:
        cmd = "sudo " + cmd

    logger.info("Executing: %s", cmd)

    return subprocess.check_output(
        shlex.split(cmd),
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )


# ==========================================================
# Parsing
# ==========================================================

def parse_nmap_output(output):
    """Extract (ip, mac) pairs from nmap output."""
    discovered = []
    current_ip = None

    for line in output.splitlines():
        host_match = HOST_RE.match(line)
        if host_match:
            current_ip = host_match.group(1)
            discovered.append((current_ip, None))
            continue

        if current_ip:
            mac_match = MAC_RE.search(line)
            if mac_match:
                mac = mac_match.group(1).lower()
                discovered[-1] = (current_ip, mac)
                current_ip = None

    return discovered


# ==========================================================
# Cleanup
# ==========================================================

def cleanup_stalled_scans():
    """Mark stuck scans as failed."""
    updated = ScanRun.objects.filter(
        status="running",
        finished_at__isnull=True
    ).update(
        status="failed",
        finished_at=timezone.now()
    )

    if updated:
        logger.info("Cleaned %d stalled scans.", updated)

    return updated


# ==========================================================
# Main scan entry
# ==========================================================

def scan_network(network_range=None, use_sudo=False, triggered_by="manual"):
    """
    Main scan workflow.
    """

    # 1️⃣ Cleanup DB state first
    cleanup_stalled_scans()

    # 2️⃣ Remove orphan lock if no scan is running in DB
    if os.path.exists(LOCK_FILE):
        if not ScanRun.objects.filter(status="running").exists():
            try:
                os.remove(LOCK_FILE)
                logger.warning("Removed orphan lock file.")
            except OSError:
                pass

    # 3️⃣ Load network range from SystemConfig
    if not network_range:
        config = SystemConfig.load_config()
        network_range = config.default_network_range

    # 4️⃣ Acquire lock
    if not acquire_lock():
        logger.warning("Scan blocked: already running.")
        return {
            "status": "locked",
            "message": "Scan already running",
        }

    # 5️⃣ Create ScanRun
    scan_run = ScanRun.objects.create(
        status="running",
        network_range=network_range,
        triggered_by=triggered_by,
    )

    try:
        logger.info(
            "Starting scan: %s (triggered_by=%s)",
            network_range,
            triggered_by,
        )

        raw_output = run_nmap_scan(network_range, use_sudo)
        discovered = parse_nmap_output(raw_output)

        hosts_discovered = len(discovered)
        created = 0
        updated = 0

        with transaction.atomic():
            known_devices = {
                d.mac.lower(): d
                for d in Device.objects.exclude(mac__isnull=True)
            }

            seen_macs = []

            for ip, mac in discovered:
            
                device = None

                if mac:
                    seen_macs.append(mac)

                    if mac in known_devices:
                        device = known_devices[mac]
                        device.ip = ip
                        device.status = "online"
                        device.last_seen = timezone.now()
                        device.save(update_fields=["ip", "status", "last_seen"])
                        updated += 1
                    else:
                        device = Device.objects.create(
                            ip=ip,
                            mac=mac,
                            status="unknown",
                            last_seen=timezone.now(),
                        )
                        created += 1

                ScanLog.objects.create(
                    scan_run=scan_run,
                    device=device,
                    ip=ip,
                    mac=mac,
                    status="online",
                )
            offline_marked = Device.objects.exclude(mac__in=seen_macs).exclude(mac__isnull=True).update(status="offline")

        # 6️⃣ Mark completed
        scan_run.status = "completed"
        scan_run.finished_at = timezone.now()
        scan_run.hosts_discovered = hosts_discovered
        scan_run.devices_created = created
        scan_run.devices_updated = updated
        scan_run.devices_offline = offline_marked
        scan_run.save()

        return {
            "hosts_discovered": hosts_discovered,
            "created": created,
            "updated": updated,
            "offline_marked": offline_marked,
        }

    except Exception:
        scan_run.status = "failed"
        scan_run.finished_at = timezone.now()
        scan_run.save()
        raise

    finally:
        release_lock()
        logger.info("Scan lock released.")