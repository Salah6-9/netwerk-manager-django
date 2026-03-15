from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import SupportTicket
from devices.models import Device
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from users.models import Office, Department, Profile

User = get_user_model()

@login_required
def tickets_list(request):

    if request.user.is_staff:
        tickets = SupportTicket.objects.all().order_by("-created_at")

    else:
        tickets = SupportTicket.objects.filter(
            user=request.user
        ).order_by("-created_at")

    return render(request, "support/list.html", {
        "tickets": tickets
    })


@login_required
def ticket_detail(request, ticket_id):

    ticket = get_object_or_404(SupportTicket, id=ticket_id)

    if not request.user.is_staff and ticket.user != request.user:
        return render(request, "403.html")

    return render(request, "support/detail.html", {
        "ticket": ticket
    })


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from devices.models import Device
from users.models import Department, Office, Profile
from .models import SupportTicket

User = get_user_model()


@login_required
def create_ticket(request):

    departments = Department.objects.all()
    offices = Office.objects.all()
    users = User.objects.select_related("profile").all()
    devices = Device.objects.select_related("user").all()

    if request.method == "POST":

        user_id = request.POST.get("user")
        device_id = request.POST.get("device")

        title = request.POST.get("title")
        description = request.POST.get("description")

        user = User.objects.get(id=user_id)

        device = None
        if device_id:
            device = Device.objects.get(id=device_id)

        SupportTicket.objects.create(
            user=user,
            device=device,
            title=title,
            description=description
        )

        return redirect("tickets_list")

    return render(request, "support/create.html", {
        "departments": departments,
        "offices": offices,
        "users": users,
        "devices": devices
    })

def offices_by_department(request, department_id):

    offices = Office.objects.filter(department_id=department_id)

    data = [
        {
            "id": office.id,
            "name": office.name
        }
        for office in offices
    ]

    return JsonResponse(data, safe=False)


def users_by_office(request, office_id):

    profiles = Profile.objects.filter(office_id=office_id)

    data = [
        {
            "id": p.user.id,
            "username": p.user.username
        }
        for p in profiles
    ]

    return JsonResponse(data, safe=False)