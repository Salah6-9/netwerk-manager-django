from django.contrib import admin
from .models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "ip",
        "mac",
        "status",
        "device_number",
        "office",
        "user",
        "is_active",
    )