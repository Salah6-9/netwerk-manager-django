from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta

from monitoring.models import MonitoringConfig
from notifications.models import Notification


WINDOW_MINUTES = 5
ALERT_COOLDOWN = 10


def create_alert(device, title, message):

    recent_alert = Notification.objects.filter(
        device=device,
        title=title,
        created_at__gte=timezone.now() - timedelta(minutes=ALERT_COOLDOWN)
    ).exists()

    if not recent_alert:

        Notification.objects.create(
            device=device,
            title=title,
            content=message,
            type="system",
            to_user=device.user
        )


def check_device_alerts(device):

    config = MonitoringConfig.load()

    recent_metrics = device.metrics.filter(
        timestamp__gte=timezone.now() - timedelta(minutes=WINDOW_MINUTES)
    )

    if recent_metrics.count() < 3:
        return

    averages = recent_metrics.aggregate(
        avg_cpu=Avg("cpu_usage"),
        avg_ram=Avg("ram_usage"),
        avg_disk=Avg("disk_usage"),
        avg_temp=Avg("cpu_temperature")
    )

    avg_cpu = averages["avg_cpu"]
    avg_ram = averages["avg_ram"]
    avg_disk = averages["avg_disk"]
    avg_temp = averages["avg_temp"]

    if avg_cpu and avg_cpu > config.cpu_threshold:

        create_alert(
            device,
            "High CPU Usage",
            f"Average CPU usage over last {WINDOW_MINUTES} minutes is {avg_cpu:.2f}%"
        )

    if avg_ram and avg_ram > config.ram_threshold:

        create_alert(
            device,
            "High RAM Usage",
            f"Average RAM usage over last {WINDOW_MINUTES} minutes is {avg_ram:.2f}%"
        )

    if avg_disk and avg_disk > config.disk_threshold:

        create_alert(
            device,
            "Disk Almost Full",
            f"Average disk usage over last {WINDOW_MINUTES} minutes is {avg_disk:.2f}%"
        )

    if avg_temp and avg_temp > config.temperature_threshold:

        create_alert(
            device,
            "High CPU Temperature",
            f"Average CPU temperature over last {WINDOW_MINUTES} minutes is {avg_temp:.2f}°C"
        )