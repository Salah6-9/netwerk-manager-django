from django.db import models
from devices.models import Device
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
User = get_user_model()

class ScanLog(models.Model):
    device = models.ForeignKey(
        Device, on_delete=models.CASCADE,
        related_name="scan_logs"
    )
    scan_run = models.ForeignKey(
        "ScanRun", on_delete=models.CASCADE, 
        related_name="logs"
    )

    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="offline")

    def __str__(self):
        return f"{self.device.mac} - {self.status} @ {self.timestamp}"

class ScanRun(models.Model):

    STATUS_CHOICES = [
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    TRIGGER_CHOICES = [
        ("manual", "Manual"),
        ("cron", "Cron"),
        ("api", "API"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    initiated_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    triggered_by=models.CharField(
        max_length=20,
        choices=TRIGGER_CHOICES,
        default="manual"
    )
    network_range = models.CharField(max_length=50)
    hosts_discovered = models.IntegerField(default=0)
    devices_created = models.IntegerField(default=0)
    devices_updated = models.IntegerField(default=0)
    devices_offline = models.IntegerField(default=0)

    def __str__(self):
        return f"ScanRun #{self.id} ({self.status})"

class SystemConfig(models.Model):
    default_network_range = models.CharField(
        max_length=50,
        default ="192.168.1.0/24"
    )
    def __str__(self):
        return "System Configuration"
    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configurations"

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SystemConfig, self).save(*args, **kwargs)
    @classmethod
    def load_config(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class DeviceStatus(models.Model):
    """
    Real-time status of a device (latest metrics).
    Only one row per device.
    """
    device = models.OneToOneField(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="Status"
    )

    cpu_usage = models.FloatField()
    ram_usage = models.FloatField()
    disk_usage = models.FloatField()

    network_in = models.FloatField()
    network_out = models.FloatField()

    cpu_temperature = models.FloatField(null=True, blank=True)

    uptime = models.IntegerField(help_text="System uptime in seconds")

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Status for {self.device}"


class DeviceMetric(models.Model):
    """
    Historical performance metrics of a device.
    """
    device = models.ForeignKey(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="metrics"
    )

    cpu_usage = models.FloatField()
    ram_usage = models.FloatField()
    disk_usage = models.FloatField()

    network_in = models.FloatField()
    network_out = models.FloatField()

    cpu_temperature = models.FloatField(null=True, blank=True)

    uptime = models.IntegerField(help_text="System uptime in seconds")

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["device", "-timestamp"])
        ]

    def __str__(self):
        return f"{self.device} @ {self.timestamp}"


class MonitoringConfig(models.Model):
    """
    Singleton model storing monitoring thresholds and agent configuration.
    """

    cpu_threshold = models.IntegerField(default=90)
    ram_threshold = models.IntegerField(default=95)
    disk_threshold = models.IntegerField(default=90)

    temperature_threshold = models.IntegerField(default=85)

    agent_interval = models.IntegerField(
        default=60,
        help_text="Agent reporting interval (seconds)"
    )

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Monitoring Configuration"


class DeviceEnrollmentRequest(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    mac = models.CharField(max_length=17)
    ip = models.GenericIPAddressField()

    hostname = models.CharField(max_length=100)
    os = models.CharField(max_length=50)
    agent_version = models.CharField(max_length=20)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)