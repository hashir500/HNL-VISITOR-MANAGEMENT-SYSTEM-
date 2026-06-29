from django.db import models

# system table model
class SystemSettings(models.Model):
    company_name = models.CharField(max_length=150)
    company_domain = models.CharField(max_length=150, blank=True, null=True)
    primary_color = models.CharField(max_length=20, default="#cb0c9f")
    secondary_color = models.CharField(max_length=20, default="#8392ab")
    logo_color = models.CharField(max_length=20, default="#ffffff")
    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name