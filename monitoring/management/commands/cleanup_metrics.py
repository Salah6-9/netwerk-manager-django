from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from monitoring.models import DeviceMetric


RETENTION_DAYS = 7


class Command(BaseCommand):
    help = "Delete device metrics older than retention window"

    def handle(self, *args, **options):

        threshold = timezone.now() - timedelta(days=RETENTION_DAYS)

        queryset = DeviceMetric.objects.filter(
            timestamp__lt=threshold
        )

        deleted_count, _ = queryset.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted_count} old metrics (older than {RETENTION_DAYS} days)"
            )
        )
