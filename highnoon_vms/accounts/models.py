from django.db import models

# Create your models here.

class user(models.Model):
    userid = models.AutoField(primary_key= True)
    username = models.CharField(max_length= 150)
    email = models.CharField(max_length= 150)
    password = models.CharField(max_length= 20)
    role = models.CharField(max_length= 50)
