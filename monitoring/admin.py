from django.contrib import admin
from .models import ScanLog, ScanRun, SystemConfig
# Register your models here.
admin.site.register(ScanLog)
admin.site.register(SystemConfig)