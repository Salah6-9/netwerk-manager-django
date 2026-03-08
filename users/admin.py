from django.contrib import admin
from .models import Profile, Department, Office


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "office")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ("name", "department")