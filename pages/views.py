from django.shortcuts import render
from . models import Contact
from .forms import ContactForm
#from django.http import HttpResponse
# Create your views here.

def home(request):
    context = { 'name01': 'SOOL', 'name02': 'ALI' }
    return render(request, 'pages/home.html', context)

def aboutme(request):
    return render(request, 'pages/about.html')

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'pages/contact.html', {'form': ContactForm(), 'success': True})
    else:
        form = ContactForm()
    return render(request, 'pages/contact.html', {'form': form})

    
 
