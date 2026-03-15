from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import SupportTicket , TicketMessage
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
from django.views.decorators.http import require_POST
User = get_user_model()


@login_required
def create_ticket(request):

    departments = Department.objects.all()

    device = None
    selected_department = None
    selected_office = None
    selected_user = None

    device_id = request.GET.get("device") or request.POST.get("device")

    if device_id:

        device = get_object_or_404(
            Device.objects.select_related(
                "user__profile__office__department"
            ),
            id=device_id
        )

        if device.user and device.user.profile and device.user.profile.office:

            selected_user = device.user
            selected_office = device.user.profile.office
            selected_department = selected_office.department

    if request.method == "POST":

        title = request.POST.get("title")
        description = request.POST.get("description")

        if request.user.is_staff:

            department_id = request.POST.get("department")
            office_id = request.POST.get("office")
            user_id = request.POST.get("user")

            department = get_object_or_404(Department, id=department_id)

            office = get_object_or_404(
                Office,
                id=office_id,
                department=department
            )

            profile = get_object_or_404(
                Profile.objects.select_related("user"),
                user_id=user_id,
                office=office
            )

            user = profile.user

        else:

            user = request.user

        # validate device ownership
        if device_id:

            device = get_object_or_404(
                Device,
                id=device_id,
                user=user
            )

        ticket = SupportTicket.objects.create(
            user=user,
            device=device,
            title=title,
            description=description
        )
        TicketMessage.objects.create(
            ticket=ticket,
            author=user,
            content=description
        )

        return redirect("tickets_list")

    return render(request, "support/create.html", {
        "departments": departments,
        "device": device,
        "selected_department": selected_department,
        "selected_office": selected_office,
        "selected_user": selected_user
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

    profiles = Profile.objects.filter(office_id=office_id).select_related("user")

    data = [
        {
            "id": p.user.id,
            "username": p.user.username
        }
        for p in profiles
    ]

    return JsonResponse(data, safe=False)


@login_required
@require_POST
def add_ticket_message(request, ticket_id):

    ticket = get_object_or_404(SupportTicket, id=ticket_id)

    if not request.user.is_staff and ticket.user != request.user :
        return render(request, "403.html")

    content = request.POST.get("content")

    if content:

        TicketMessage.objects.create(
            ticket=ticket,
            author=request.user,
            content=content
        )

    return redirect("ticket_detail", ticket_id=ticket.id)