from django.db import models


class SystemSettings(models.Model):
    company_name = models.CharField(max_length=150)
    company_name_short = models.CharField(max_length=50, blank=True, null=True)
    company_domain = models.CharField(max_length=150, blank=True, null=True)

    primary_color = models.CharField(max_length=20, default="#cb0c9f")
    secondary_color = models.CharField(max_length=20, default="#8392ab")
    logo_color = models.CharField(max_length=20, default="#ffffff")

    password_algorithm = models.CharField(max_length=50, default="PBKDF2")
    session_timeout = models.IntegerField(default=30)
    password_expiry_days = models.IntegerField(default=90)
    password_min_length = models.IntegerField(default=8)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name