from django.db import models
from visitors.models import visitor, visitor_card
from employees.models import employee


class visit(models.Model):
    visit_id = models.AutoField(primary_key=True)

    visitor = models.ForeignKey(visitor, on_delete=models.CASCADE, null=True, blank=True)
    employee = models.ForeignKey(employee, on_delete=models.SET_NULL, null=True, blank=True)

    visitor_card = models.ForeignKey(
        visitor_card,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    visit_purpose = models.CharField(max_length=255)
    check_in_time = models.DateTimeField(auto_now_add=True)
    check_out_time = models.DateTimeField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("Checked In", "Checked In"),
            ("Checked Out", "Checked Out"),
        ],
        default="Checked In"
    )

    def __str__(self):
        return f"{self.visitor} visiting {self.employee}"