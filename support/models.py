from django.db import models
from users.models import User
from devices.models import Device
from notifications.models import Notification


class SupportTicket(models.Model):

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets"
    )

    notification = models.ForeignKey(
        Notification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets"
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open"
    )

    ticket_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
    priority = models.CharField(
    max_length=20,
    choices=[
        ("low","Low"),
        ("medium","Medium"),
        ("high","High"),
        ("critical","Critical"),
    ],
    default="medium"
    )   

    def save(self, *args, **kwargs):

        # Save first to get ID
        if not self.id:
            super().save(*args, **kwargs)

        # Generate ticket code if not exists
        if not self.ticket_code:
            self.ticket_code = f"TKT-{self.id:04d}"
            super().save(update_fields=["ticket_code"])

        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_code} - {self.title}"

    class Meta:
        ordering = ["-created_at"]