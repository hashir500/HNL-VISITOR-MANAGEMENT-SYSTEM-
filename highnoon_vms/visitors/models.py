from django.db import models

# Create your models here.

# visitor_card model
class visitor_card(models.Model):
    id = models.AutoField(primary_key=True)
    CRD_No = models.CharField(max_length=50, unique=True)
    CRD_Desc = models.CharField(max_length=150)
    CRD_Active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.CRD_No} - {self.CRD_Desc}"
    
# visitor model
class visitor(models.Model):
    visitor_id = models.AutoField(primary_key=True)
    visitor_name = models.CharField(max_length=100)
    visitor_phone = models.CharField(max_length=15)
    visitor_cnic = models.CharField(max_length=20, unique=True, null=True, blank=True)
    visitor_address = models.CharField(max_length=255)
    visitor_created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.visitor_name