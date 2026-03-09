from django.urls import path
from . import views
urlpatterns = [
    path ('', views.clients, name='clients'),  # /clients/ URL mapped to clients view
    path ('client', views.client, name='client'),  # /client/ URL mapped to client view 

]