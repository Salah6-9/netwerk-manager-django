from django.db import models

# Create your models here.

class Client(models.Model):

    offices = [
            ('HR','HR') , ('IT','IT') , ('Finance','Finance') , ('Marketing','Marketing'),
            ('Sales','Sales') ,('Maintenance','Maintenance') , ('Design','Design'),
            ('Development','Development') , ('Testing','Testing')  , ('Research','Research'),
        ]
    name = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20 , verbose_name='Phone Number',default="00000000")
    devicenumber = models.CharField(max_length=100, verbose_name='Device Number')     
    post = models.CharField()
    macaddress = models.CharField(max_length=100, verbose_name='MAC Address'    )
    ipaddress = models.CharField(max_length=100, verbose_name='IP Address'      )
    image = models.ImageField(upload_to='client_images/', null=True, blank=True)
    active = models.BooleanField(default=True)
    office = models.CharField(max_length=100, verbose_name='Office Name' , null=True, blank=True,choices=offices)
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Client'
        ordering = ['name']
