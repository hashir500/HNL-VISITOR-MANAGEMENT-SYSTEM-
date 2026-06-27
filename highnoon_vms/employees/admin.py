from django.contrib import admin
from .models import department
from .models import employee

# Register your models here.

admin.site.register(department)
admin.site.register(employee)