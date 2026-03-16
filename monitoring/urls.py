from django.urls import path
from monitoring.api.views import MetricsIngestView, DeviceEnrollmentView
from monitoring import views

urlpatterns = [
    path("api/metrics/", MetricsIngestView.as_view(), name="metrics-ingest"),
    
    path(
        "api/device-enrollment/",
        DeviceEnrollmentView.as_view(),
        name="device-enrollment"
    ),
    
    path("api/device-metrics/<int:device_id>/", views.device_metrics_api, name="device_metrics_api"),
]