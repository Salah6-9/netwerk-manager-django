from django.db import models
from users.models import User
from devices.models import Device
from notifications.models import Notification
from django.contrib.auth import get_user_model
User = get_user_model()


class SupportTicket(models.Model):

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    TARGET_CHOICES = [
        ("user", "Specific User"),
        ("office", "Entire Office"),
        ("department", "Entire Department"),
    ]

    target_type = models.CharField(
        max_length=20,
        choices=TARGET_CHOICES,
        default="user"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tickets",
        null=True,
        blank=True
    )

    office = models.ForeignKey(
        "users.Office",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets"
    )

    department = models.ForeignKey(
        "users.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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


class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ticket_messages"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Msg #{self.id} on {self.ticket.ticket_code}"