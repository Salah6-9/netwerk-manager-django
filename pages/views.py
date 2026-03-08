from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.http import HttpResponseForbidden,HttpResponseNotAllowed
import os
from monitoring.models import ScanRun
from monitoring.scanner.nmap_scanner import scan_network, cleanup_stalled_scans, LOCK_FILE
from devices.models import Device
def is_admin(user):
    return user.is_superuser or user.groups.filter(name="Admin").exists()

@login_required
def trigger_scan(request):
    
    #allow only post
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    
    #allow only admin
    if not is_admin(request.user):
        return HttpResponseForbidden("You are not authorized to perform this action")
    
    
    scan_network(
        network_range=None,
        triggered_by="manual", )
    return redirect("dashboard")


@login_required
def dashboard(request):
    cleanup_stalled_scans()

    admin = request.user.groups.filter(name="Admin").exists()

    if admin:
        latest_scan = ScanRun.objects.order_by("-started_at").first()
        scan_running = ScanRun.objects.filter(
            status="running",
            finished_at__isnull=True
        ).exists()
        devices = Device.objects.all()
        template = "dashboard_admin.html"
    else:
        latest_scan = None
        scan_running = False
        devices = Device.objects.filter(user=request.user)
        template = "dashboard_employee.html"

    context = {
        "latest_scan": latest_scan,
        "scan_running": scan_running,
        "devices": devices,
    }

    return render(request, template, context)
 
LOCK_FILE = "/tmp/network_scan.lock"
def dashboard_status_api(request):
    """
    Read-only API endpoint.
    Returns current dashboard scan status as JSON.
    """

    #Get latest scan
    latest_scan = ScanRun.objects.order_by("-started_at").first()

    # Determine if scan is running
    scan_running = False

    if latest_scan and latest_scan.status == "running":
        scan_running = True

    scan_running = ScanRun.objects.filter(
        status="running",
        finished_at__isnull=True
    ).exists()
    #  Prepare response payload
    data = {
        "scan_running": scan_running,
        "latest_scan": None,
    }

    if latest_scan:
        data["latest_scan"] = {
            "status": latest_scan.status,
            "started_at": latest_scan.started_at,
            "finished_at": latest_scan.finished_at,
            "hosts_discovered": latest_scan.hosts_discovered,
            "devices_created": latest_scan.devices_created,
            "devices_updated": latest_scan.devices_updated,
            "devices_offline": latest_scan.devices_offline,
        }

    return JsonResponse(data)