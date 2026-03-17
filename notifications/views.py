from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.http import HttpResponseNotAllowed
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
# Create your views here.

def is_admin(user):
    return user.is_superuser or user.groups.filter(name="Admin").exists()


@login_required
def notifications_count(request):

    if is_admin(request.user):

        count = Notification.objects.filter(
            resolved=False
        ).count()

    else:

        count = Notification.objects.filter(
            to_user=request.user,
            resolved=False
        ).count()

    return render(
        request,
        "partials/notifications_count.html",
        {"count": count}
    )

@login_required
def notifications_center(request):
    if not is_admin(request.user):
        notifications = Notification.objects.select_related(
            "device",
            "to_user"
        ).filter(to_user=request.user).order_by("-created_at")

    else:
        notifications = Notification.objects.select_related(
            "device",
            "to_user"
        ).order_by("-created_at")

    # Monitoring alerts
    monitoring_alerts = notifications.filter(type="system")

    # Support notifications
    support_notifications = notifications.filter(type="support")

    active_alerts = monitoring_alerts.filter(resolved=False).count()
    resolved_alerts = monitoring_alerts.filter(resolved=True).count()

    context = {
        "monitoring_alerts": monitoring_alerts,
        "support_notifications": support_notifications,
        "active_alerts": active_alerts,
        "resolved_alerts": resolved_alerts,
        "is_admin": is_admin(request.user)
    }

    return render(request, "admin/notifications.html", context)

@login_required
@user_passes_test(is_admin)
def resolve_notification(request, pk):

    notification = Notification.objects.get(id=pk)

    notification.resolved = True
    notification.resolved_at = timezone.now()

    notification.save()

    return redirect("notifications_center")
    
@login_required
@user_passes_test(is_admin)
def delete_notification(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
        
    notification = Notification.objects.get(id=pk)

    notification.delete()

    return redirect("notifications_center")