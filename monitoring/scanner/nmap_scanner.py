import os
import time
import re
import shlex
import subprocess
import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from devices.models import Device
from monitoring.models import ScanLog

logger = logging.getLogger(__name__)

# ==========================================================
# File-based lock configuration
# ==========================================================
LOCK_FILE = "/tmp/network_scan.lock"

# ==========================================================
# Regex patterns for parsing nmap output
# ==========================================================
HOST_RE = re.compile(r"^Nmap scan report for\s+(\d+\.\d+\.\d+\.\d+)", re.MULTILINE)
MAC_RE = re.compile(r"MAC Address:\s*([0-9A-Fa-f:]{17})")


# ==========================================================
# Lock helpers
# ==========================================================
def acquire_lock():
    """
    Acquire scan lock.
    Returns False if a scan is already running.
    """
    if os.path.exists(LOCK_FILE):
        return False

    with open(LOCK_FILE, "w") as f:
        f.write(str(time.time()))

    return True


def release_lock():
    """
    Release scan lock if exists.
    """
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


# ==========================================================
# Nmap execution
# ==========================================================
def run_nmap_scan(network_range, use_sudo=False, timeout=240):
    """
    Execute nmap ARP scan and return raw output.
    """
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
    """
    Parse nmap output and return list of (ip, mac).
    """
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
    - Run nmap
    - Parse results
    - Update database
    - Create scan logs
    """

    # 🔐 Acquire lock
    if not acquire_lock():
        logger.warning("Network scan already running. New scan aborted.")
        return {
            "status": "locked",
            "message": "Scan already running",
        }

    try:
        logger.info(
            "Starting network scan: range=%s triggered_by=%s",
            network_range,
            triggered_by,
        )

        raw_output = run_nmap_scan(network_range, use_sudo=use_sudo)
        discovered = parse_nmap_output(raw_output)

        hosts_discovered = len(discovered)
        created = 0
        updated = 0

        with transaction.atomic():
            known_devices = {d.mac.lower(): d for d in Device.objects.exclude(mac__isnull=True)}
            seen_macs = []

            for ip, mac in discovered:
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
                        Device.objects.create(
                            ip=ip,
                            mac=mac,
                            status="unknown",
                            last_seen=timezone.now(),
                        )
                        created += 1

            offline_marked = Device.objects.exclude(mac__in=seen_macs).update(status="offline")

            for device in Device.objects.filter(mac__in=seen_macs):
                ScanLog.objects.create(
                    device=device,
                    status=device.status,
                )

        return {
            "hosts_discovered": hosts_discovered,
            "created": created,
            "updated": updated,
            "offline_marked": offline_marked,
        }

    finally:
        # 🔓 Always release lock
        release_lock()
        logger.info("Network scan lock released")

