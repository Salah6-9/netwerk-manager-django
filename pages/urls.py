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
    alerts_center,
    resolve_alert,
    delete_alert,
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

    path("alerts/", alerts_center, name="alerts_center"),

    path("alerts/<int:pk>/resolve/", resolve_alert, name="resolve_alert"),

    path("alerts/<int:pk>/delete/", delete_alert, name="delete_alert"),

]