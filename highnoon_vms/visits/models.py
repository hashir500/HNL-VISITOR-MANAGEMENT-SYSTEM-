from django.db import models
from django.utils import timezone  # Added to handle custom timestamps
from visitors.models import visitor, visitor_card
from masters.models import sys_emp_master

class visit(models.Model):
    visit_id = models.AutoField(primary_key=True)


    visitor = models.ForeignKey(visitor, on_delete=models.CASCADE, null=True, blank=True)
    employee = models.ForeignKey(sys_emp_master, on_delete=models.SET_NULL, null=True, blank=True)
    visitor_card = models.ForeignKey(
        visitor_card,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    visit_purpose = models.CharField(max_length=255)
    

    check_in_time = models.DateTimeField(default=timezone.now)
    check_out_time = models.DateTimeField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("Checked In", "Checked In"),
            ("Checked Out", "Checked Out"),
        ],
        default="Checked In"
    )

    is_backlog = models.BooleanField(default=False)

    class Meta:
        
        permissions = [
            ("can_view_backlogs", "Can view backlogs"),
        ]

    def __str__(self):
        return f"{self.visitor} visiting {self.employee}"