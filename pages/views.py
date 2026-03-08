from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from monitoring.models import ScanRun
from monitoring.scanner.nmap_scanner import scan_network, cleanup_stalled_scans, LOCK_FILE
from devices.models import Device
def is_admin(user):
    return user.is_superuser or user.groups.filter(name="Admin").exists()
 
@login_required
def trigger_scan(request):
    if request.method == "POST":
        scan_network(
            network_range="192.168.1.0/24",
            triggered_by="dashboard", )
    return redirect("dashboard")


@login_required
def dashboard(request):
    latest_scan = (
    ScanRun.objects.filter(status="completed")
    .order_by("-finished_at")
    .first()
)
    scan_running = ScanRun.objects.filter(
     status="running",
     finished_at__isnull=True
    ).exists()

    return render(
        request,
        "dashboard.html",
        {
            "latest_scan": latest_scan,
            "scan_running": scan_running,
        },
    )