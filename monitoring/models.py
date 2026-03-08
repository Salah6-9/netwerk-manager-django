from django.db import models
from devices.models import Device

class ScanLog(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="scan_logs")
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

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    hosts_discovered = models.IntegerField(default=0)
    devices_created = models.IntegerField(default=0)
    devices_updated = models.IntegerField(default=0)
    devices_offline = models.IntegerField(default=0)

    def __str__(self):
        return f"ScanRun #{self.id} ({self.status})"