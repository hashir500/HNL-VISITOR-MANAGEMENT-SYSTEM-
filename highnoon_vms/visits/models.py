from django.db import models
from visitors.models import visitor,visitor_card
from employees.models import employee

# Create your models here.

# visits model

class visit(models.Model):
    status_choices= [
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    visit_id = models.AutoField(primary_key= True)

    vistor_id = models.ForeignKey(
        visitor,
        on_delete= models.CASCADE,
        related_name= 'visits'
    )

    employee_id = models.ForeignKey(
        employee,
        on_delete= models.CASCADE,
        related_name= 'visits'
    )

    card_id = models.ForeignKey(
        visitor_card,
        on_delete= models.CASCADE,
        related_name= 'visits'
    )

    purpose_of_visit = models.CharField(max_length=255)
    check_in_time = models.DateTimeField(auto_now_add= True)
    check_out_time = models.DateTimeField(null= True, blank= True)
    status = models.CharField(max_length= 20, choices= status_choices, default= "active")

    def __str__(self):
        return f"{self.visitor_id} visiting {self.employee_id}"