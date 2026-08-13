from django.db.models import Q

from .models import Notification


def workspace_context(request):
    notifications = Notification.objects.filter(is_read=False)
    if request.user.is_authenticated:
        notifications = notifications.filter(Q(user=request.user) | Q(user__isnull=True))
    else:
        notifications = notifications.filter(user__isnull=True)
    return {
        "workspace_notifications": notifications[:5],
        "workspace_notification_count": notifications.count(),
    }
