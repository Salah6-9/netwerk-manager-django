from .models import Notification

def notifications(request):

    if not request.user.is_authenticated:
        return {}

    user_notifications = Notification.objects.filter(
        to_user=request.user,
        resolved=False
    )

    return {
        "notifications_count": user_notifications.count(),
        "notifications": user_notifications.order_by("-created_at")[:10],
    }