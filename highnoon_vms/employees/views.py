from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required

from .models import department, employee


@login_required
@permission_required("employees.view_department", raise_exception=True)
def department_list(request):
    departments = department.objects.all()
    return render(request, "employees/department_list.html", {"departments": departments})


@login_required
@permission_required("employees.add_department", raise_exception=True)
def department_create(request):
    if request.method == "POST":
        department_name = request.POST.get("department_name")

        if department_name:
            department.objects.create(department_name=department_name)

        return redirect("department_list")

    return render(request, "employees/department_form.html")


@login_required
@permission_required("employees.change_department", raise_exception=True)
def department_update(request, department_id):
    dept = get_object_or_404(department, department_id=department_id)

    if request.method == "POST":
        department_name = request.POST.get("department_name")

        if department_name:
            dept.department_name = department_name
            dept.save()

        return redirect("department_list")

    return render(request, "employees/department_form.html", {"dept": dept})


@login_required
@permission_required("employees.delete_department", raise_exception=True)
def department_delete(request, department_id):
    dept = get_object_or_404(department, department_id=department_id)

    if request.method == "POST":
        dept.delete()
        return redirect("department_list")

    return render(request, "employees/department_confirm_delete.html", {"dept": dept})


@login_required
@permission_required("employees.view_employee", raise_exception=True)
def employee_list(request):
    employees = employee.objects.all()
    departments = department.objects.all()

    return render(request, "employees/employee_list.html", {
        "employees": employees,
        "departments": departments,
    })


@login_required
@permission_required("employees.add_employee", raise_exception=True)
def employee_create(request):
    departments = department.objects.all()

    if request.method == "POST":
        employee.objects.create(
            employee_name=request.POST.get("employee_name"),
            employee_email=request.POST.get("employee_email"),
            employee_phone=request.POST.get("employee_phone"),
            employee_designation=request.POST.get("employee_designation"),
            employee_department=department.objects.get(
                pk=request.POST.get("employee_department")
            )
        )

        return redirect("employee_list")

    return render(request, "employees/employee_form.html", {
        "departments": departments
    })


@login_required
@permission_required("employees.change_employee", raise_exception=True)
def employee_update(request, employee_id):
    emp = get_object_or_404(employee, pk=employee_id)
    departments = department.objects.all()

    if request.method == "POST":
        emp.employee_name = request.POST.get("employee_name")
        emp.employee_email = request.POST.get("employee_email")
        emp.employee_phone = request.POST.get("employee_phone")
        emp.employee_designation = request.POST.get("employee_designation")
        emp.employee_department = department.objects.get(
            pk=request.POST.get("employee_department")
        )
        emp.save()

        return redirect("employee_list")

    return render(request, "employees/employee_form.html", {
        "employee": emp,
        "departments": departments,
    })


@login_required
@permission_required("employees.delete_employee", raise_exception=True)
def employee_delete(request, employee_id):
    emp = get_object_or_404(employee, pk=employee_id)

    if request.method == "POST":
        emp.delete()
        return redirect("employee_list")

    return render(request, "employees/employee_confirm_delete.html", {
        "employee": emp,
    })