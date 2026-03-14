from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden,HttpResponseNotAllowed
from rest_framework.authtoken.models import Token 
from django.shortcuts import render, redirect , get_object_or_404
from monitoring.models import ScanRun ,DeviceEnrollmentRequest , ScanLog, DeviceMetric , DeviceStatus
from monitoring.scanner.nmap_scanner import scan_network, cleanup_stalled_scans, LOCK_FILE
from devices.models import Device 
from users.models import Department
from notifications.models import Notification
import json
import os
from django.http import JsonResponse



def is_admin(user):
    return user.is_superuser or user.groups.filter(name="Admin").exists()

## admin functions --------------------------------------------------------------------
# ___________________________________________________________________________________

## display requests
@login_required
@user_passes_test(is_admin)
def enrollment_requests(request):

    enrollments = DeviceEnrollmentRequest.objects.all().order_by("-created_at")

    pending = DeviceEnrollmentRequest.objects.filter(status="pending").count()
    approved = DeviceEnrollmentRequest.objects.filter(status="approved").count()
    rejected = DeviceEnrollmentRequest.objects.filter(status="rejected").count()

    context = {
        "enrollments": enrollments,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
    }

    return render(request, "admin/enrollments.html", context)

# approve request
@login_required
@user_passes_test(is_admin)
def approve_enrollment(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    enrollment = get_object_or_404(DeviceEnrollmentRequest, id=pk)

    enrollment.status = "approved"
    enrollment.save()

    return redirect("enrollments")

# reject request
@login_required
@user_passes_test(is_admin)
def reject_enrollment(request, pk):

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    enrollment = get_object_or_404(DeviceEnrollmentRequest, id=pk)

    enrollment.status = "rejected"
    enrollment.save()

    return redirect("enrollments")

# Delete request
@login_required
@user_passes_test(is_admin)
def delete_enrollment(request, pk):

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    enrollment = get_object_or_404(DeviceEnrollmentRequest, id=pk)

    if enrollment.status == "pending" :
        return redirect("enrollments")

    enrollment.delete()

    return redirect("enrollments")

#Device functions --------------------------------------------------------------------
@login_required
@user_passes_test(is_admin)
def devices_list(request):

    departments = Department.objects.all()

    devices = Device.objects.select_related(
        "office",
        "user"
    )

    context = {
        "departments": departments,
        "devices": devices
    }

    return render(request, "admin/devices.html", context)

#device details
@login_required
@user_passes_test(is_admin)
def device_details(request, pk):
    device = get_object_or_404(Device, id=pk)
    status = DeviceMetric.objects.filter(device=device).first()
    user_token = Token.objects.get(user=device.user)
    metrics = DeviceMetric.objects.filter(device=device).order_by("-timestamp")[:50]
    metrics = list(reversed(metrics))
    time_data = [m.timestamp.strftime("%H:%M:%S") for m in metrics]
    cpu_data = [m.cpu_usage or 0 for m in metrics]
    ram_data = [m.ram_usage or 0 for m in metrics]
    disk_data = [m.disk_usage or 0 for m in metrics]
    temp_data = [m.cpu_temperature or 0 for m in metrics]
    alerts = Notification.objects.filter(
        to_user=request.user,
        type="system"
    ).order_by("-created_at")[:10]
    context = {
        "device": device,
        "status": status,
        "metrics": metrics,
        "user_token" : user_token.key,
        "time_data": json.dumps(time_data),
        "cpu_data": json.dumps(cpu_data),
        "ram_data": json.dumps(ram_data),
        "disk_data": json.dumps(disk_data),
        "temp_data": json.dumps(temp_data),
        "alerts": alerts,
    }
    return render(request, "admin/device_details.html", context)

#Device alerts
@login_required
@user_passes_test(is_admin)
def alerts_center(request):

    alerts = Notification.objects.filter(
        type="system"
    ).order_by("-created_at")[:100]

    context = {
        "alerts": alerts
    }

    return render(request, "admin/alerts.html", context)
# ------------------------------------------------------------------------------------------

## Employee functions --------------------------------------------------------------------
@login_required
#@user_passes_test(is_admin)
def setup_agent(request):
     user_token = Token.objects.get(user=request.user)
     context = {
         "user_token" : user_token.key
     }
     return render(request, "employee/setup_agent.html", context)


# trigger scan
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

    latest_scan = ScanRun.objects.order_by("-started_at").first()
    total_devices = Device.objects.count()
    total_online_devices = Device.objects.filter(status="online").count()
    total_offline_devices = Device.objects.filter(status="offline").count()
    total_unknown_devices = Device.objects.filter(status="unknown").count()
    discovered_devices = []

    if latest_scan:
        discovered_devices = ScanLog.objects.filter(scan_run=latest_scan)

    if admin:

        scan_running = ScanRun.objects.filter(
            status="running",
            finished_at__isnull=True
        ).exists()

        devices = Device.objects.all()

        template = "admin/dashboard.html"

    else:

        scan_running = False
        devices = Device.objects.filter(user=request.user)
        device_status = []
        for device in devices:
            status =  DeviceStatus.objects.filter(device=device).first()
            device_status.append(
                {
                    "device": device,
                    "status": status,
                }
            )
        context = {
            "device_status": device_status,
        }
        template = "employee/dashboard.html"

    context = {
        "latest_scan": latest_scan,
        "scan_running": scan_running,
        "devices": devices,
        "discovered_devices": discovered_devices,
        "total_devices": total_devices,
        "total_online_devices": total_online_devices,
        "total_offline_devices": total_offline_devices,
        "total_unknown_devices": total_unknown_devices,
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