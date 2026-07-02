from django.db import models


class DashboardPermission(models.Model):
    class Meta:
        managed = False
        permissions = [
            ("view_dashboard", "Can view dashboard"),
        ]