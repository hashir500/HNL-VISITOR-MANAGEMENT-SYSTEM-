from django.contrib import admin
from .models import visitor_card
from .models import visitor

# Register your models here.

admin.site.register(visitor_card)
admin.site.register(visitor)
