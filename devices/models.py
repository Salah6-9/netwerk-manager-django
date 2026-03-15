from django.db import models
from django.contrib.auth.models import User
import secrets
from django.core.exceptions import ValidationError


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
    agent_token = models.CharField(
        max_length=128, blank=True,
        null=True, unique=True
    )
    hostname = models.CharField(max_length=255, blank=True, null=True)
    os = models.CharField(max_length=50, blank=True, null=True)
    # validate that device office must match user office
    def clean(self):

        if self.user and self.office:

            if self.user.profile.office != self.office:

                raise ValidationError({
                    "office": "Device office must match user's office"
                })
    # save -- generate agent token
    def save(self, *args, **kwargs):

        if self.user and self.office:

            if self.user.profile.office != self.office:
                raise ValueError("Device office must match user office")

        super().save(*args, **kwargs)
    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.mac}"
        return f"Unknown - {self.mac}"
    
