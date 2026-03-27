from django.core.management.base import BaseCommand
from devices.models import Device
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Synchronize and recalculate device statuses based on agent heartbeats and scanner results'

    def handle(self, *args, **options):
        devices = Device.objects.filter(is_active=True)
        total = devices.count()
        updated = 0
        
        self.stdout.write(f"Starting status sync for {total} active devices...")
        
        for device in devices:
            old_status = device.status
            new_status = device.update_status()
            
            if old_status != new_status:
                updated += 1
                logger.info(f"Device {device.mac} changed status: {old_status} -> {new_status}")
        
        self.stdout.write(self.style.SUCCESS(f"Successfully synced statuses. {updated} devices updated."))
