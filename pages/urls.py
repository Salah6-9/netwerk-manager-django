from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Root URL mapped to index view
    path('about', views.aboutme, name='aboutme'),  # /about/ URL mapped to about view
    path('contact', views.contact, name='contact'),  # /contact/ URL mapped to contact view

]