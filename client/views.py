from django.shortcuts import render
from . models import Client

# Create your views here.

def clients(request):
    return render(request, 'client/clients.html', {'clnt': Client.objects.all()})   

def client(request):
    return render(request, 'client/client.html')   

 