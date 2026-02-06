from django.urls import path
from .views import dashboard
from .import views


urlpatterns = [
    path("dashboard/", dashboard, name="dashboard"),
    path("trigger-scan/", views.trigger_scan, name="trigger_scan"),
]