from django.urls import path
from monitoring.api.views import MetricsIngestView, DeviceEnrollmentView

urlpatterns = [
    path("api/metrics/", MetricsIngestView.as_view(), name="metrics-ingest"),
    path(
        "api/device-enrollment/",
        DeviceEnrollmentView.as_view(),
        name="device-enrollment"
    )
]