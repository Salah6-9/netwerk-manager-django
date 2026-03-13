from monitoring.models import MonitoringConfig
from notifications.models import Notification
from django.utils import timezone
from datetime import timedelta


def create_alert(device, title, message):

    recent_alert = Notification.objects.filter(
        to_user=device.user,
        title=title,
        created_at__gte=timezone.now() - timedelta(minutes=5)
    ).exists()

    if not recent_alert:
        Notification.objects.create(
            title=title,
            content=message,
            type="system",
            to_user=device.user
        )


def check_device_alerts(device, metric):

    config = MonitoringConfig.load()

    if metric.cpu_usage > config.cpu_threshold:
        create_alert(
            device,
            "High CPU Usage",
            f"{device.hostname} CPU usage is {metric.cpu_usage}%"
        )

    if metric.ram_usage > config.ram_threshold:
        create_alert(
            device,
            "High RAM Usage",
            f"{device.hostname} RAM usage is {metric.ram_usage}%"
        )

    if metric.disk_usage > config.disk_threshold:
        create_alert(
            device,
            "Disk Almost Full",
            f"{device.hostname} disk usage is {metric.disk_usage}%"
        )

    if metric.cpu_temperature and metric.cpu_temperature > config.temperature_threshold:
        create_alert(
            device,
            "High CPU Temperature",
            f"{device.hostname} temperature is {metric.cpu_temperature}°C"
        )