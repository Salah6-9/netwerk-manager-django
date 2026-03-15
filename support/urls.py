from django.urls import path
from . import views

urlpatterns = [

    path("", views.tickets_list, name="tickets_list"),

    path("create/", views.create_ticket, name="create_ticket"),

    path("<int:ticket_id>/", views.ticket_detail, name="ticket_detail"),

    # APIs
    path("api/offices/<int:department_id>/", views.offices_by_department, name="offices_by_department"),
    path("api/users/<int:office_id>/", views.users_by_office, name="users_by_office"),

    path("<int:ticket_id>/message/", views.add_ticket_message, name="add_ticket_message"),

]