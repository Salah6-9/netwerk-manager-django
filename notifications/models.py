from django.db import models
from users.models import User
from devices.models import Device

class Notification(models.Model):
    TYPE_CHOICES = [
        ("manual", "Manual"),
        ("system", "System"),
    ]

    title = models.CharField(max_length=100)
    content = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="manual")
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True
    )    
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} → {self.to_user.name}"
