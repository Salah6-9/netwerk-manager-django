from django.urls import path
from . import views

urlpatterns = [
    path("count/", views.notifications_count, name="notifications_count"),
    path("notifications/<int:pk>/resolve/", views.resolve_notification, name="resolve_notification"),
    path("notifications/<int:pk>/delete/", views.delete_notification, name="delete_notification"),
    path("notifications/delete-all/", views.delete_all_notifications, name="delete_all_notifications"),
    path("dropdown/", views.notifications_dropdown, name="notifications_dropdown"),
    path("mark-as-read/<int:pk>/", views.mark_notification_read, name="mark_notification_read"),
    path("mark-all-read/", views.mark_all_read, name="mark_all_read"),
]