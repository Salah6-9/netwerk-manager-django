from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name



class Office(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="offices"
    )

    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["department", "name"],
                name="unique_office_per_department"
            )
        ]

    def __str__(self):
        return f"{self.department.name} - {self.name}"

class Profile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    office = models.ForeignKey(
        "Office", on_delete=models.SET_NULL,
        blank=True, null=True
    )
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20 , blank = True)
    position = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to="profiles/", blank=True, null=True)

    def __str__(self):
        return f"Profile: {self.user.username}"



User = get_user_model()
@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

