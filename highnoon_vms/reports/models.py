from django.db import models

# Create your models here.
from django.db import models


class ReportPermission(models.Model):
    class Meta:
        managed = False
        permissions = [
            ("view_reports", "Can view reports"),
            ("download_reports", "Can download reports"),
        ]