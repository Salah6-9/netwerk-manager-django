from notifications.models import Notification
from pages.views import is_admin


def notifications(request):

    if not request.user.is_authenticated:
        return {"notifications_count": 0}

    if is_admin(request.user):
        # Admins see all system alerts + notifications specifically for them
        from django.db.models import Q
        count = Notification.objects.filter(
            is_read=False
        ).filter(
            Q(type="system") | Q(to_user=request.user)
        ).count()
    else:
        count = Notification.objects.filter(
            to_user=request.user,
            is_read=False
        ).count()

    return {"notifications_count": count}