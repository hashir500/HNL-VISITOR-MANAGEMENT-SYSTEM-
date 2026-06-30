from django.db import models

# Create your models here.

# visitor_card model
class visitor_card(models.Model):
    card_id = models.AutoField(primary_key=True)
    card_number = models.CharField(max_length=20, unique= True)
    card_color = models.CharField(max_length=50)
    card_access_level = models.CharField(max_length=100)

    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.card_color} ({self.card_number})"
    
# visitor model

class visitor(models.Model):
    visitor_id = models.AutoField(primary_key= True)
    visitor_name = models.CharField(max_length= 100)
    visitor_email = models.EmailField(unique= True)
    visitor_phone = models.CharField(max_length= 15)
    visitor_address = models.CharField(max_length=255, blank=True, null=True)
    visitor_created_at = models.DateTimeField(auto_now_add= True)

    def __str__(self):
        return self.visitor_name

