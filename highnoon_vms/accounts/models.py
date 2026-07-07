from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ("local", "Local Database"),
        ("m365", "Microsoft 365"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        default="local",
    )

    def __str__(self):
        return f"{self.user.email} ({self.get_account_type_display()})"