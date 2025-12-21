 # monitoring/management/commands/scan_network.py
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from devices.models import Device
from monitoring.models import ScanLog

import scapy.all as scapy
import logging

# إعداد logger لتسجيل العمليات في ملف logs/scan.log
logger = logging.getLogger(__name__)
handler = logging.FileHandler("logs/scan.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Scan the local network and update devices in database (optimized & secure)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--range",
            type=str,
            default="192.168.1.1/24",
            help="حدد نطاق الشبكة المراد فحصه (مثلاً: 192.168.1.1/24)",
        )

    def handle(self, *args, **options):
        # ✅ 1. التحقق من بيئة التشغيل
        if not settings.DEBUG:
            raise CommandError("🚫 لا يمكن تشغيل الفحص في وضع الإنتاج دون تصريح صريح.")

        network_range = options["range"]
        self.stdout.write(self.style.WARNING(f"🔍 بدء الفحص للشبكة: {network_range}"))
        logger.info(f"Starting network scan for {network_range}")

        try:
            # ✅ 2. تنفيذ فحص ARP
            arp_request = scapy.ARP(pdst=network_range)
            broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
            arp_request_broadcast = broadcast / arp_request
            answered = scapy.srp(arp_request_broadcast, timeout=3, verbose=False)[0]

            discovered = []
            for _, received in answered:
                discovered.append((received.psrc, received.hwsrc))

            self.stdout.write(self.style.SUCCESS(f"📡 تم اكتشاف {len(discovered)} جهاز(ات)."))
            logger.info(f"Discovered {len(discovered)} devices.")

            # ✅ 3. معالجة النتائج داخل معاملة واحدة (Transaction)
            with transaction.atomic():
                all_macs_online = [mac for _, mac in discovered]
                known_devices = {d.mac: d for d in Device.objects.all()}

                new_devices = []
                updated_devices = []

                for ip, mac in discovered:
                    if mac in known_devices:
                        # تحديث الجهاز الحالي
                        device = known_devices[mac]
                        device.ip = ip
                        device.status = "online"
                        device.last_seen = timezone.now()
                        updated_devices.append(device)
                    else:
                        # إنشاء جهاز جديد (غير معروف)
                        new_devices.append(
                            Device(ip=ip, mac=mac, status="unknown", last_seen=timezone.now())
                        )

                # ✅ 4. تحديث الأجهزة دفعة واحدة (Bulk)
                if new_devices:
                    Device.objects.bulk_create(new_devices)
                    logger.info(f"Added {len(new_devices)} new device(s).")

                if updated_devices:
                    Device.objects.bulk_update(updated_devices, ["ip", "status", "last_seen"])
                    logger.info(f"Updated {len(updated_devices)} existing device(s).")

                # ✅ 5. الأجهزة غير المكتشفة = Offline
                offline_count = Device.objects.exclude(mac__in=all_macs_online).update(
                    status="offline"
                )
                if offline_count:
                    logger.info(f"Marked {offline_count} device(s) as offline.")

                # ✅ 6. سجل الفحص (ScanLog)
                for d in updated_devices + new_devices:
                    ScanLog.objects.create(device=d, status=d.status)

            self.stdout.write(self.style.SUCCESS("✅ الفحص اكتمل بنجاح."))
            logger.info("Network scan completed successfully.")

        except Exception as e:
            logger.error(f"❌ خطأ أثناء الفحص: {e}")
            raise CommandError(f"حدث خطأ أثناء الفحص: {e}")

