from monitoring.models import MonitoringConfig
from notifications.models import Notification


def check_device_alerts(device, metric):

    config = MonitoringConfig.load_config()

    if metric.cpu_usage > config.cpu_threshold:

        Notification.objects.create(
            title="High CPU Usage",
            message=f"{device.hostname} CPU usage is {metric.cpu_usage}%",
            type="system",
            to_user=device.user
        )

    if metric.ram_usage > config.ram_threshold:

        Notification.objects.create(
            title="High RAM Usage",
            message=f"{device.hostname} RAM usage is {metric.ram_usage}%",
            type="system",
            to_user=device.user
        )

    if metric.disk_usage > config.disk_threshold:

        Notification.objects.create(
            title="Disk Almost Full",
            message=f"{device.hostname} disk usage is {metric.disk_usage}%",
            type="system",
            to_user=device.user
        )

    
    if metric.cpu_temperature and metric.cpu_temperature > config.temperature_threshold:

        Notification.objects.create(
            title="High Temperature",
            message=f"{device.hostname} temperature is {metric.cpu_temperature}",
            type="system",
            to_user=device.user
        )
