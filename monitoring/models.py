from django.db import models
from devices.models import Device

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
        
