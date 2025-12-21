# monitoring/management/commands/scan_network_nmap.py
import re
import shlex
import subprocess
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import logging
import os

from devices.models import Device
from monitoring.models import ScanLog

logger = logging.getLogger(__name__)
LOG_FILE = getattr(settings, "NETWORK_SCAN_LOG", os.path.join(settings.BASE_DIR, "logs", "scan_nmap.log"))
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
fh = logging.FileHandler(LOG_FILE)
fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(fh)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Scan the local network with nmap (ARP scan) and update devices. Usage: python manage.py scan_network_nmap --range 10.42.0.0/24"

    def add_arguments(self, parser):
        parser.add_argument("--range", type=str, required=True, help="Network range CIDR to scan, e.g. 10.42.0.0/24")
        parser.add_argument("--sudo", action="store_true", help="If set, command will attempt to prepend sudo to nmap call (useful if running from venv).")

    def handle(self, *args, **options):
        network_range = options["range"]
        use_sudo = options["sudo"]

        # Optional safety: prevent running accidentally in production
        if not settings.DEBUG:
            self.stdout.write(self.style.WARNING("Running in non-DEBUG mode — make sure you intend to run this on production."))
            # do not block; adjust policy as you prefer

        # Build nmap command:
        # -sn : ping scan (no port scan)
        # -PR : ARP ping (on local LAN) — good for ARP discovery
        cmd = f"nmap -sn -PR {shlex.quote(network_range)}"
        if use_sudo:
            cmd = "sudo " + cmd

        self.stdout.write(self.style.WARNING(f"🔍 Running: {cmd}"))
        logger.info(f"Starting nmap scan for {network_range} (sudo={use_sudo})")

        try:
            output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT, text=True, timeout=240)
        except subprocess.CalledProcessError as e:
            logger.error("nmap failed: %s", e.output if hasattr(e, "output") else str(e))
            raise CommandError(f"nmap returned non-zero status: {e}")
        except subprocess.TimeoutExpired:
            logger.error("nmap scan timed out")
            raise CommandError("nmap scan timed out")

        # Parse nmap output
        # Sample relevant blocks:
        # Nmap scan report for 10.42.0.203
        # Host is up (0.0030s latency).
        # MAC Address: AE:BE:0E:B7:6F:9D (Vendor)
        host_re = re.compile(r"^Nmap scan report for\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", re.MULTILINE)
        mac_re = re.compile(r"MAC Address:\s*([0-9A-Fa-f:]{17})")

        lines = output.splitlines()
        discovered = []  # list of tuples (ip, mac_or_none)
        current_ip = None
        for line in lines:
            m = host_re.match(line)
            if m:
                current_ip = m.group(1).strip()
                # initialize with no-mac; may be filled by subsequent MAC line
                discovered.append((current_ip, None))
                continue
            if current_ip:
                mm = mac_re.search(line)
                if mm:
                    mac = mm.group(1).lower()
                    # replace the most recent tuple's mac
                    discovered[-1] = (discovered[-1][0], mac)
                    current_ip = None  # reset for safety

        self.stdout.write(self.style.SUCCESS(f"📡 nmap discovered {len(discovered)} host(s)."))
        logger.info(f"nmap discovered {len(discovered)} hosts: {discovered}")

        # database update: bulk create/update
        with transaction.atomic():
            all_macs_seen = []
            # Load known devices into dict keyed by mac (lowercase)
            known_devices_qs = Device.objects.all()
            known_by_mac = {d.mac.lower(): d for d in known_devices_qs if d.mac}
            updated = []
            to_create = []
            # If model has last_seen attribute:
            supports_last_seen = hasattr(Device, "last_seen") or "last_seen" in [f.name for f in Device._meta.get_fields()]

            for ip, mac in discovered:
                if mac:
                    all_macs_seen.append(mac)
                    if mac in known_by_mac:
                        dev = known_by_mac[mac]
                        dev.ip = ip
                        dev.status = "online"
                        if supports_last_seen:
                            try:
                                dev.last_seen = timezone.now()
                            except Exception:
                                pass
                        updated.append(dev)
                    else:
                        # create Device object to bulk_create; some models may require different fields
                        kwargs = {"ip": ip, "mac": mac, "status": "unknown"}
                        if supports_last_seen:
                            kwargs["last_seen"] = timezone.now()
                        to_create.append(Device(**kwargs))
                else:
                    # IP found but no MAC (rare). We can try to match by IP
                    try:
                        dev = Device.objects.filter(ip=ip).first()
                        if dev:
                            dev.status = "online"
                            if supports_last_seen:
                                dev.last_seen = timezone.now()
                            updated.append(dev)
                        else:
                            # create with unknown mac
                            kwargs = {"ip": ip, "mac": f"unknown-{ip}", "status": "unknown"}
                            if supports_last_seen:
                                kwargs["last_seen"] = timezone.now()
                            to_create.append(Device(**kwargs))
                    except Exception:
                        logger.exception("Error handling entry without MAC for %s", ip)

            # bulk create and update
            created_count = 0
            updated_count = 0
            if to_create:
                Device.objects.bulk_create(to_create)
                created_count = len(to_create)
                logger.info(f"Created {created_count} devices (bulk).")

            if updated:
                # ensure the pk's exist before bulk_update (they do for updated)
                Device.objects.bulk_update(updated, ["ip", "status"] + (["last_seen"] if supports_last_seen else []))
                updated_count = len(updated)
                logger.info(f"Updated {updated_count} devices (bulk).")

            # mark others offline
            if all_macs_seen:
                offline_count = Device.objects.exclude(mac__in=all_macs_seen).update(status="offline")
            else:
                offline_count = 0

            # create ScanLog entries for discovered hosts
            # For newly created devices, ensure we fetch them (simpler approach)
            processed_macs = [m for _, m in discovered if m]
            if processed_macs:
                devices_for_logs = Device.objects.filter(mac__in=processed_macs)
            else:
                ips = [ip for ip, mac in discovered]
                devices_for_logs = Device.objects.filter(ip__in=ips)

            for dev in devices_for_logs:
                try:
                    ScanLog.objects.create(device=dev, status=dev.status, timestamp=timezone.now())
                except TypeError:
                    # if ScanLog timestamp auto_now_add, ignore timestamp param
                    ScanLog.objects.create(device=dev, status=dev.status)

        self.stdout.write(self.style.SUCCESS(f"✅ Scan complete. created={created_count} updated={updated_count} offline_marked={offline_count}"))
        logger.info(f"Scan result summary: created={created_count} updated={updated_count} offline_marked={offline_count}")

