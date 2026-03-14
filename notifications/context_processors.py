from notifications.models import Notification


def alerts_counter(request):

    if not request.user.is_authenticated:
        return {}

    if request.user.is_staff:
        count = Notification.objects.filter(resolved=False).count()
    else:
        count = Notification.objects.filter(
            to_user=request.user,
            resolved=False
        ).count()

    return {
        "alerts_counter": count
    }
