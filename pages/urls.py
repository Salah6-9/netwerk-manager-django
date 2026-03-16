from django.urls import path
from .views import (
    dashboard,
    dashboard_status_api,
    enrollment_requests,
    approve_enrollment,
    reject_enrollment,
    delete_enrollment,
    devices_list,
    device_details,
    setup_agent,
    notifications_center,
    resolve_alert,
    delete_notification,
    dashboard_stats,
    notifications_count,
)
from . import views

urlpatterns = [

    path("dashboard/", dashboard, name="dashboard"),

    path("trigger-scan/", views.trigger_scan, name="trigger_scan"),

    path("api/dashboard/status/", dashboard_status_api, name="dashboard_status_api"),

    path("enrollments/", enrollment_requests, name="enrollments"),

    path("enrollments/<int:pk>/approve/", approve_enrollment, name="approve_enrollment"),

    path("enrollments/<int:pk>/reject/", reject_enrollment, name="reject_enrollment"),

    path("enrollments/<int:pk>/delete/", delete_enrollment, name="delete_enrollment"),

    path("devices/", devices_list, name="devices_list"),

    path("devices/<int:pk>/", device_details, name="device_details"),

    path("setup-agent/", setup_agent, name="setup_agent"),

    # Notifications Center
    path("notifications/", notifications_center, name="notifications_center"),

    # Monitoring Alert Actions
    path("alerts/<int:pk>/resolve/", resolve_alert, name="resolve_alert"),

    path("notifications/<int:pk>/delete/", views.delete_notification, name="delete_notification"),

    path("dashboard/stats/", dashboard_stats, name="dashboard_stats"),

    path("notifications/count/", notifications_count, name="notifications_count"),
]