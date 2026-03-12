import secrets
from django.db.models.signals import post_save
from django.dispatch import receiver

from devices.models import Device
from .models import DeviceEnrollmentRequest


@receiver(post_save, sender=DeviceEnrollmentRequest)
def handle_enrollment_approval(sender, instance, created, **kwargs):

    if instance.status != "approved":
        return

    if Device.objects.filter(mac=instance.mac).exists():
        return

    token = secrets.token_hex(32)

    Device.objects.create(
        ip=instance.ip,
        mac=instance.mac,
        device_number=instance.hostname,
        user=instance.user,
        agent_token=token,
        is_active=True,
        hostname=instance.hostname,
        os=instance.os,
    )