from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from monitoring.models import ScanRun
from monitoring.scanner.nmap_scanner import scan_network


@login_required
def dashboard(request):
    if request.method == "POST":
        scan_network(
            network_range="192.168.1.0/24",
            triggered_by="manual",
        )
        return redirect("dashboard")

    last_scan = ScanRun.objects.order_by("-started_at").first()

    context = {
        "last_scan": last_scan,
    }
    return render(request, "dashboard.html", context)