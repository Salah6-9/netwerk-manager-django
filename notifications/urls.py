from django.urls import path
from . import views

urlpatterns = [
    path("count/", views.notifications_count, name="notifications_count"),
    path("notifications/<int:pk>/resolve/", views.resolve_notification, name="resolve_notification"),
    path("notifications/<int:pk>/delete/", views.delete_notification, name="delete_notification"),
    path("notifications/delete-all/", views.delete_all_notifications, name="delete_all_notifications"),
]