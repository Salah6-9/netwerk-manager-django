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

# Regex patterns for parsing nmap output
HOST_RE = re.compile(r"^Nmap scan report for\s+(\d+\.\d+\.\d+\.\d+)", re.MULTILINE)
MAC_RE = re.compile(r"MAC Address:\s*([0-9A-Fa-f:]{17})")


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
        timeout=timeout
    )


def parse_nmap_output(output):
    """
    Parse nmap output and return list of (ip, mac_or_none).
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
                discovered[-1] = (current_ip, mac_match.group(1).lower())
                current_ip = None

    return discovered


def update_devices_from_scan(discovered):
    """
    Update Device table based on discovered hosts.
    """
    supports_last_seen = "last_seen" in [f.name for f in Device._meta.get_fields()]

    known_devices = {
        d.mac.lower(): d
        for d in Device.objects.exclude(mac__isnull=True)
    }

    to_create = []
    to_update = []
    seen_macs = []

    with transaction.atomic():
        for ip, mac in discovered:
            if mac:
                seen_macs.append(mac)

                if mac in known_devices:
                    dev = known_devices[mac]
                    dev.ip = ip
                    dev.status = "online"
                    if supports_last_seen:
                        dev.last_seen = timezone.now()
                    to_update.append(dev)
                else:
                    data = {
                        "ip": ip,
                        "mac": mac,
                        "status": "unknown",
                    }
                    if supports_last_seen:
                        data["last_seen"] = timezone.now()
                    to_create.append(Device(**data))

        if to_create:
            Device.objects.bulk_create(to_create)

        if to_update:
            Device.objects.bulk_update(
                to_update,
                ["ip", "status"] + (["last_seen"] if supports_last_seen else [])
            )

        offline_count = Device.objects.exclude(mac__in=seen_macs).update(
            status="offline"
        )

        logs = [
            ScanLog(device=device, status=device.status)
            for device in Device.objects.filter(mac__in=seen_macs)
        ]
        if logs:
            ScanLog.objects.bulk_create(logs)

    return {
        "hosts_discovered": len(discovered),
        "created": len(to_create),
        "updated": len(to_update),
        "offline_marked": offline_count,
    }


def scan_network(network_range, use_sudo=False, triggered_by="manual"):
    """
    Public API: scan network and update database.
    """
    logger.info(
        "Network scan started (triggered_by=%s, range=%s)",
        triggered_by,
        network_range,
    )

    output = run_nmap_scan(network_range, use_sudo)
    discovered = parse_nmap_output(output)
    result = update_devices_from_scan(discovered)

    logger.info("Network scan finished: %s", result)
    return result
