from django.shortcuts import render, redirect, get_object_or_404
from .models import department


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

def department_delete(request, department_id):
    dept = get_object_or_404(department, department_id=department_id)

    if request.method == "POST":
        dept.delete()
        return redirect("department_list")

    return render(request, "employees/department_confirm_delete.html", {"dept": dept})