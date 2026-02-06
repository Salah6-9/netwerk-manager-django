from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

import os
from monitoring.models import ScanRun
from monitoring.scanner.nmap_scanner import scan_network, cleanup_stalled_scans, LOCK_FILE

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
    # Cleanup any stalled runs before rendering
    cleanup_stalled_scans()

    scan_running = ScanRun.objects.filter(
     status="running",
     finished_at__isnull=True
    ).exists() or os.path.exists(LOCK_FILE)

    return render(
        request,
        "dashboard.html",
        {
            "latest_scan": latest_scan,
            "scan_running": scan_running,
        },
    )