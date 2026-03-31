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
    
    # New tracking fields
    last_agent_heartbeat = models.DateTimeField(null=True, blank=True)
    last_scan_seen = models.DateTimeField(null=True, blank=True)

    def update_status(self, save=True):
        """
        Logic:
        - Online: Agent reported in last 5m OR Scanner saw it in last 15m.
        - Offline: Agent silent for >10m AND Scanner silent for >20m.
        - Unknown: No data from either.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        is_agent_online = self.last_agent_heartbeat and (now - self.last_agent_heartbeat) < timedelta(minutes=5)
        is_scanner_online = self.last_scan_seen and (now - self.last_scan_seen) < timedelta(minutes=15)

        if is_agent_online or is_scanner_online:
            new_status = "online"
        elif not self.last_agent_heartbeat and not self.last_scan_seen:
            new_status = "unknown"
        else:
            # Check if definitely offline (both had a chance to report but didn't)
            agent_stale = not self.last_agent_heartbeat or (now - self.last_agent_heartbeat) > timedelta(minutes=10)
            scanner_stale = not self.last_scan_seen or (now - self.last_scan_seen) > timedelta(minutes=20)
            
            if agent_stale and scanner_stale:
                new_status = "offline"
            else:
                # Still in a grace period or only one source is stale
                new_status = "online" if (is_agent_online or is_scanner_online) else self.status

        if self.status != new_status:
            self.status = new_status
            if save:
                self.save(update_fields=["status"])
        
        return new_status

    # validate that device office must match user office
    def clean(self):
        if self.user and self.office:
            try:
                if self.user.profile.office != self.office:
                    raise ValidationError({
                        "office": "Device office must match user's office"
                    })
            except (AttributeError, User.profile.RelatedObjectDoesNotExist):
                # If user has no profile, we can't validate office alignment this way
                pass
    # save -- generate agent token
    def save(self, *args, **kwargs):
        if self.user and self.office:
            try:
                if self.user.profile.office != self.office:
                    raise ValueError("Device office must match user office")
            except (AttributeError, User.profile.RelatedObjectDoesNotExist):
                pass
        super().save(*args, **kwargs)
    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.mac}"
        return f"Unknown - {self.mac}"
