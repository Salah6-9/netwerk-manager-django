from django.db import models
from devices.models import Device

class ScanLog(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="scan_logs")
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="offline")

    def __str__(self):
        return f"{self.device.mac} - {self.status} @ {self.timestamp}"
