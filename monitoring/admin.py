from django.contrib import admin
from .models import (
    ScanLog,
    ScanRun,
    SystemConfig,
    DeviceStatus,
    DeviceMetric,
    MonitoringConfig,
    DeviceEnrollmentRequest,
)


# -------------------------
# Scan Layer
# -------------------------

@admin.register(ScanRun)
class ScanRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "started_at",
        "finished_at",
        "status",
        "hosts_discovered",
        "devices_created",
        "devices_updated",
    )
    ordering = ("-started_at",)


@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
    list_display = (
        "device",
        "status",
        "scan_run",
    )
    list_filter = ("status",)


admin.site.register(SystemConfig)


# -------------------------
# Monitoring Layer
# -------------------------

@admin.register(DeviceMetric)
class DeviceMetricAdmin(admin.ModelAdmin):
    list_display = (
        "device",
        "cpu_usage",
        "ram_usage",
        "disk_usage",
        "network_in",
        "network_out",
        "cpu_temperature",
        "timestamp",
    )
    list_filter = ("device",)
    ordering = ("-timestamp",)


@admin.register(DeviceStatus)
class DeviceStatusAdmin(admin.ModelAdmin):
    list_display = (
        "device",
        "cpu_usage",
        "ram_usage",
        "disk_usage",
        "cpu_temperature",
        "updated_at",
    )


@admin.register(MonitoringConfig)
class MonitoringConfigAdmin(admin.ModelAdmin):
    list_display = (
        "cpu_threshold",
        "ram_threshold",
        "disk_threshold",
        "temperature_threshold",
        "agent_interval",
    )

@admin.register(DeviceEnrollmentRequest)
class DeviceEnrollmentRequestAdmin(admin.ModelAdmin):

    list_display = (
        "hostname",
        "ip",
        "mac",
        "status",
        "created_at",
    )

    list_filter = ("status",)

    search_fields = ("hostname", "ip", "mac")

    fields = (
        "hostname",
        "ip",
        "mac",
        "os",
        "agent_version",
        "status",
        "created_at",
    )

    readonly_fields = ("created_at",)