from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.http import JsonResponse

from .models import SupportTicket, TicketMessage
from devices.models import Device
from users.models import Office, Department, Profile
from notifications.models import Notification
from pages.views import is_admin


User = get_user_model()


# -------------------------
# Tickets List
# -------------------------

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


# -------------------------
# Ticket Detail
# -------------------------

@login_required
def ticket_detail(request, ticket_id):

    ticket = get_object_or_404(SupportTicket, id=ticket_id)

    if not request.user.is_staff and ticket.user != request.user:
        return render(request, "403.html")

    return render(request, "support/detail.html", {
        "ticket": ticket
    })


# -------------------------
# Create Ticket
# -------------------------

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

        # Create ticket
        ticket = SupportTicket.objects.create(
            user=user,
            device=device,
            title=title,
            description=description
        )

        # First message
        TicketMessage.objects.create(
            ticket=ticket,
            author=request.user,
            content=description
        )

        # -----------------
        # Notification Logic
        # -----------------

        if request.user.is_staff :
            recipients = [user]
        else:
            recipients = User.objects.filter(is_staff=True)

        for r in recipients:
            if r == request.user:

                Notification.objects.create(
                    title="New Support Ticket",
                    content=f"Ticket {ticket.ticket_code} created",
                    type="support",
                    to_user=r,
                    device=device
                )

        return redirect("tickets_list")

    return render(request, "support/create.html", {
        "departments": departments,
        "device": device,
        "selected_department": selected_department,
        "selected_office": selected_office,
        "selected_user": selected_user
    })


# -------------------------
# AJAX Offices
# -------------------------

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


# -------------------------
# AJAX Users
# -------------------------

def users_by_office(request, office_id):

    profiles = Profile.objects.filter(
        office_id=office_id
    ).select_related("user")

    data = [
        {
            "id": p.user.id,
            "username": p.user.username
        }
        for p in profiles
    ]

    return JsonResponse(data, safe=False)


# -------------------------
# Add Ticket Message
# -------------------------

@login_required
@require_POST
def add_ticket_message(request, ticket_id):

    ticket = get_object_or_404(SupportTicket, id=ticket_id)

    if not request.user.is_staff and ticket.user != request.user:
        return render(request, "403.html")

    content = request.POST.get("content")

    if content:

        message = TicketMessage.objects.create(
            ticket=ticket,
            author=request.user,
            content=content
        )

        # Notification logic
        recipients = []
        if is_admin(request.user):
            recipients = [ticket.user]
        else:
            recipients = list(User.objects.filter(is_staff=True).all())

      
        if recipients:

            for r in recipients:
                if r != request.user:
                    Notification.objects.create(
                        title="New reply on ticket",
                        content=f"{request.user.username} replied to ticket {ticket.ticket_code}",
                        type="support",
                        to_user=r,
                    device=ticket.device
                )

    return redirect("ticket_detail", ticket_id=ticket.id)


# -------------------------
# Update Ticket Status
# -------------------------

@login_required
@require_POST
def update_ticket_status(request, ticket_id):

    ticket = get_object_or_404(SupportTicket, id=ticket_id)

    if not request.user.is_staff:
        return render(request, "403.html")

    new_status = request.POST.get("status")

    allowed_status = ["open", "in_progress", "resolved", "closed"]

    if new_status in allowed_status:
        ticket.status = new_status
        ticket.save()

    return redirect("ticket_detail", ticket_id=ticket.id)


# -------------------------
# Delete Ticket
# -------------------------

@login_required
@require_POST
def delete_ticket(request, ticket_id):

    ticket = get_object_or_404(SupportTicket, id=ticket_id)

    if not request.user.is_staff and ticket.user != request.user:
        return render(request, "403.html")

    ticket.delete()

    return redirect("tickets_list")


