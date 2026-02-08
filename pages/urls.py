from django.urls import path
from .views import dashboard
from .views import dashboard_status_api
from .import views


urlpatterns = [
    path("dashboard/", dashboard, name="dashboard"),
    path("trigger-scan/", views.trigger_scan, name="trigger_scan"),
    path("api/dashboard/status/", dashboard_status_api, name="dashboard_status_api"),
]