from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from devices.models import Device
from monitoring.models import DeviceMetric


@login_required
def device_metrics_api(request, device_id):
    """
    JSON endpoint used by Chart.js to display device metrics.
    """

    device = get_object_or_404(Device, id=device_id)

    if not request.user.is_staff and device.user != request.user:
        return JsonResponse({"error": "Forbidden"}, status=403)

    range_minutes = int(request.GET.get("range_minutes", 1440))
    since = timezone.now() - timedelta(minutes=range_minutes)

    metrics = (
        DeviceMetric.objects
        .filter(device=device, timestamp__gte=since)
        .order_by("timestamp")
    )

    data = {
        "device_id": device.id,
        "range_minutes": range_minutes,
        "timestamps": [m.timestamp.strftime("%H:%M") for m in metrics],
        "cpu": [m.cpu_usage or 0 for m in metrics],
        "ram": [m.ram_usage or 0 for m in metrics],
        "disk": [m.disk_usage or 0 for m in metrics],
        "temperature": [m.cpu_temperature or 0 for m in metrics],
    }

    return JsonResponse(data)