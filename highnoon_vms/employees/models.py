from django.db import models

# Create your models here.
class department(models.Model):
    department_id = models.AutoField(primary_key = True)
    department_name = models.CharField(max_length = 100, unique = True)

    def __str__(self):
        return self.department_name