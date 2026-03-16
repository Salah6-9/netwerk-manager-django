from notifications.models import Notification
from pages.views import is_admin


def notifications(request):

    if not request.user.is_authenticated:
        return {"notifications_count": 0}

    if is_admin(request.user):

        count = Notification.objects.filter(
            resolved=False
        ).count()

    else:

        count = Notification.objects.filter(
            to_user=request.user,
            resolved=False
        ).count()

    return {"notifications_count": count}