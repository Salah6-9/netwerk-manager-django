from notifications.models import Notification

from .models import Notification


def alerts_counter(request):

    if not request.user.is_authenticated:
        return {}

    notifications = Notification.objects.filter(
        to_user=request.user,
        resolved=False
    ).order_by("-created_at")

    return {
        "notifications": notifications[:10],
        "notifications_count": notifications.count(),
    }