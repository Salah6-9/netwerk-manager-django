from django.db import models
from django.contrib.auth.models import User

class Device(models.Model):
    STATUS_CHOICES = [
        ("online", "Online"),
        ("offline", "Offline"),
        ("unknown", "Unknown"),
    ]

    user = models.ForeignKey(User, null= True,on_delete=models.CASCADE, related_name="devices")
    ip = models.GenericIPAddressField()
    mac = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="offline")

    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.mac}"
        return f"Unknown - {self.mac}"
    
