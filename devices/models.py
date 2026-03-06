from django.db import models
from django.contrib.auth.models import User

class Device(models.Model):
    STATUS_CHOICES = [
        ("online", "Online"),
        ("offline", "Offline"),
        ("unknown", "Unknown"),
    ]
    office = models.ForeignKey(
        "users.Office",
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        User, null= True,blank=True,
        on_delete=models.SET_NULL, 
        related_name="devices"
    )
    ip = models.GenericIPAddressField()
    mac = models.CharField(
        max_length=100, unique=True
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="offline"
    )
    device_number = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.mac}"
        return f"Unknown - {self.mac}"
    
