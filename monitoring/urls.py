from django.urls import path
from monitoring.api.views import MetricsIngestView

urlpatterns = [
    path("api/metrics/", MetricsIngestView.as_view(), name="metrics-ingest"),
]