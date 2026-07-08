from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from masters.models import sys_dep_master

# Create your models here.
    
# employee model
class employee(models.Model):
    employee_id = models.AutoField(primary_key= True)
    employee_name = models.CharField(max_length= 100)
    employee_email = models.EmailField(unique=True)
    employee_phone = models.CharField(max_length = 11)
    employee_designation = models.CharField(max_length= 100)

    employee_department = models.ForeignKey(
        sys_dep_master,
        on_delete= models.CASCADE,
        related_name='employees'  
    )

    employee_created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.employee_name
    

