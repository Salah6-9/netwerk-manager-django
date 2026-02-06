import os
import time
import re
import shlex
import subprocess
import logging

from django.db import transaction
from django.utils import timezone

from devices.models import Device
from monitoring.models import ScanLog, ScanRun

logger = logging.getLogger(__name__)

# ==========================================================
# File-based lock configuration
# ==========================================================
LOCK_FILE = "/tmp/network_scan.lock"
LOCK_TIMEOUT = 300  # 5 minutes


# ==========================================================
# Regex patterns for parsing nmap output
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
    """Acquire scan lock. Return False if already running."""
    if os.path.exists(LOCK_FILE):
        # Check for stale lock
        try:
            with open(LOCK_FILE, "r") as f:
                timestamp = float(f.read().strip())
                
            if time.time() - timestamp > LOCK_TIMEOUT:
                logger.warning("Found stale scan lock (age > %ds). Removing it.", LOCK_TIMEOUT)
                try:
                    os.remove(LOCK_FILE)
                except OSError:
                    # Could have been removed by another process
                    pass
            else:
                return False
        except (ValueError, OSError):
            # If we can't read the file, assume it's corrupted/stale and try to remove it
             logger.warning("Found corrupted scan lock. Removing it.")
             try:
                os.remove(LOCK_FILE)
             except OSError:
                pass


    with open(LOCK_FILE, "w") as f:
        f.write(str(time.time()))

    return True


def release_lock():
    """Release scan lock if exists."""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


# ==========================================================
# Nmap execution
# ==========================================================
def run_nmap_scan(network_range, use_sudo=False, timeout=240):
    """Execute nmap ARP scan and return raw output."""
    cmd = f"nmap -sn -PR {shlex.quote(network_range)}"
    if use_sudo:
        cmd = "sudo " + cmd

    logger.info("Running nmap command: %s", cmd)

    return subprocess.check_output(
        shlex.split(cmd),
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )


# ==========================================================
# Nmap output parsing
# ==========================================================
def parse_nmap_output(output):
    """Parse nmap output and return list of (ip, mac)."""
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
# Main scanner entry point
# ==========================================================
def scan_network(network_range, use_sudo=False, triggered_by="manual"):
    """
    Perform full network scan:
    - Acquire lock
    - Create ScanRun
    - Run nmap
    - Update devices
    - Create ScanLogs per device
    - Update ScanRun status
    """

    # 🔐 Acquire lock
    if not acquire_lock():
        logger.warning("Network scan already running.")
        return {
            "status": "locked",
            "message": "Scan already running",
        }

    # Create ScanRun
    ScanRun.objects.filter(
        status="running",
        finished_at__isnull=True
    ).update(
        status="failed",
        finished_at=timezone.now()
    )

    #  Create ScanRun (واحد فقط)
    scan_run = ScanRun.objects.create(status="running")
    try:
        logger.info(
            "Starting network scan: %s (triggered_by=%s)",
            network_range,
            triggered_by,
        )

        raw_output = run_nmap_scan(network_range, use_sudo=use_sudo)
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
                if not mac:
                    continue

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

                # ✅ Create ScanLog PER DEVICE
                ScanLog.objects.create(
                    device=device,
                    status=device.status,
                )

            offline_marked = Device.objects.exclude(
                mac__in=seen_macs
            ).update(status="offline")

        # ✅ Mark scan as completed
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
        # ❌ Mark scan as failed
        scan_run.status = "failed"
        scan_run.finished_at = timezone.now()
        scan_run.save()
        raise

    finally:
        # 🔓 Always release lock
        release_lock()
        logger.info("Network scan lock released")