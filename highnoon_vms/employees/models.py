from django.db import models
from django.shortcuts import render, redirect, get_object_or_404

# Create your models here.

# department model
class department(models.Model):
    department_id = models.AutoField(primary_key = True)
    department_name = models.CharField(max_length = 100, unique = True)

    def __str__(self):
        return self.department_name
    
# employee model
class employee(models.Model):
    employee_id = models.AutoField(primary_key= True)
    employee_name = models.CharField(max_length= 100)
    employee_email = models.EmailField(unique=True)
    employee_phone = models.CharField(max_length = 11)
    employee_cnic = models.CharField(max_length=20,unique=True)
    employee_designation = models.CharField(max_length= 100)

    employee_department = models.ForeignKey(
        department,
        on_delete= models.CASCADE,
        related_name='employees'  
    )

    employee_created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.employee_name
    


def department_list(request):
    departments = department.objects.all()
    return render(request, "employees/department_list.html", {"departments": departments})


def department_create(request):
    if request.method == "POST":
        department_name = request.POST.get("department_name")

        if department_name:
            department.objects.create(department_name=department_name)

        return redirect("department_list")

    return render(request, "employees/department_form.html")


def department_update(request, department_id):
    dept = get_object_or_404(department, department_id=department_id)

    if request.method == "POST":
        department_name = request.POST.get("department_name")

        if department_name:
            dept.department_name = department_name
            dept.save()

        return redirect("department_list")

    return render(request, "employees/department_form.html", {"dept": dept})