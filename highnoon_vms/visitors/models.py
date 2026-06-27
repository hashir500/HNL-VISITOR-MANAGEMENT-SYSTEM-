from django.db import models

# Create your models here.

class visitor_card(models.Model):
    card_id = models.AutoField(primary_key= True)
    card_color = models.CharField(max_length= 50, unique= True)
    card_access_level= models.CharField(max_length=100)

    def __str__(self):
        return self.card_color