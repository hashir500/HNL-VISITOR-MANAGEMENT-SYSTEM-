from django.shortcuts import render, redirect, get_object_or_404
import requests
import openpyxl

from django.contrib import messages
from django.conf import settings
import os
import uuid
from openpyxl import load_workbook
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password


from .models import sys_usr_system
from .models import sys_cmp_master
from .forms import CompanyMasterForm
from .models import sys_bra_master
from .forms import BranchMasterForm
from .models import sys_div_master
from .forms import DivisionMasterForm
from .models import sys_dep_master, sys_div_master
from .forms import DepartmentMasterForm
from .models import sys_emp_master
from .forms import EmployeeMasterForm
from .models import sys_pur_master
from .forms import PurposeMasterForm
from django.http import JsonResponse
from .models import sys_emp_master


# company views
def company_list(request):
    companies = sys_cmp_master.objects.all().order_by("id")
    form = CompanyMasterForm()

    return render(request, "masters/company_list.html", {
        "companies": companies,
        "form": form,
    })


def company_create(request):
    if request.method == "POST":
        form = CompanyMasterForm(request.POST)
        if form.is_valid():
            form.save()

    return redirect("company_list")


def company_update(request, pk):
    company = get_object_or_404(sys_cmp_master, pk=pk)

    if request.method == "POST":
        form = CompanyMasterForm(request.POST, instance=company)
        if form.is_valid():
            form.save()

    return redirect("company_list")


def company_delete(request, pk):
    company = get_object_or_404(sys_cmp_master, pk=pk)

    if request.method == "POST":
        company.delete()

    return redirect("company_list")

# branch views
def branch_list(request):
    branches = sys_bra_master.objects.all().order_by("bra_code")

    return render(request, "masters/branch_list.html", {
        "branches": branches,
    })


def branch_create(request):
    if request.method == "POST":
        form = BranchMasterForm(request.POST)
        if form.is_valid():
            form.save()

    return redirect("branch_list")


def branch_update(request, pk):
    branch = get_object_or_404(sys_bra_master, pk=pk)

    if request.method == "POST":
        form = BranchMasterForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()

    return redirect("branch_list")


def branch_delete(request, pk):
    branch = get_object_or_404(sys_bra_master, pk=pk)

    if request.method == "POST":
        branch.delete()

    return redirect("branch_list")


# division views
def division_list(request):
    divisions = sys_div_master.objects.all().order_by("div_code")

    return render(request, "masters/division_list.html", {
        "divisions": divisions,
    })


def division_create(request):
    if request.method == "POST":
        form = DivisionMasterForm(request.POST)
        if form.is_valid():
            form.save()

    return redirect("division_list")


def division_update(request, pk):
    division = get_object_or_404(sys_div_master, pk=pk)

    if request.method == "POST":
        form = DivisionMasterForm(request.POST, instance=division)
        if form.is_valid():
            form.save()

    return redirect("division_list")


def division_delete(request, pk):
    division = get_object_or_404(sys_div_master, pk=pk)

    if request.method == "POST":
        division.delete()

    return redirect("division_list")

# department views
def department_master_list(request):
    departments = (
        sys_dep_master.objects
        .select_related("dep_div_code")
        .all()
        .order_by("dep_code")
    )

    divisions = sys_div_master.objects.filter(div_active=True).order_by("div_desc")

    return render(request, "masters/department_list.html", {
        "departments": departments,
        "divisions": divisions,
    })


def department_master_create(request):
    if request.method == "POST":
        form = DepartmentMasterForm(request.POST)
        if form.is_valid():
            form.save()

    return redirect("department_master_list")


def department_master_update(request, pk):
    department = get_object_or_404(sys_dep_master, pk=pk)

    if request.method == "POST":
        form = DepartmentMasterForm(request.POST, instance=department)
        if form.is_valid():
            form.save()

    return redirect("department_master_list")


def department_master_delete(request, pk):
    department = get_object_or_404(sys_dep_master, pk=pk)

    if request.method == "POST":
        department.delete()

    return redirect("department_master_list")


def department_import_upload(request):
    if request.method == "POST":
        excel_file = request.FILES.get("excel_file")

        if not excel_file:
            messages.error(request, "Please upload an Excel file.")
            return redirect("department_master_list")

        upload_dir = os.path.join(settings.MEDIA_ROOT, "imports")
        os.makedirs(upload_dir, exist_ok=True)

        file_name = f"{uuid.uuid4()}_{excel_file.name}"
        file_path = os.path.join(upload_dir, file_name)

        with open(file_path, "wb+") as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)

        workbook = load_workbook(file_path)
        sheet = workbook.active

        excel_columns = []
        for cell in sheet[1]:
            if cell.value:
                excel_columns.append(str(cell.value).strip())

        request.session["department_import_file"] = file_path

        return render(request, "masters/department_import_map.html", {
            "excel_columns": excel_columns,
            "db_fields": [
                ("dep_code", "Department Code"),
                ("dep_desc", "Department Description"),
                ("dep_div_code", "Division Code"),
                ("dep_active", "Active"),
            ],
        })

    return redirect("department_master_list")


def department_import_process(request):
    if request.method == "POST":
        file_path = request.session.get("department_import_file")

        if not file_path or not os.path.exists(file_path):
            messages.error(request, "Import file not found. Please upload again.")
            return redirect("department_master_list")

        workbook = load_workbook(file_path)
        sheet = workbook.active

        headers = [str(cell.value).strip() if cell.value else "" for cell in sheet[1]]

        mapping = {
            "dep_code": request.POST.get("dep_code"),
            "dep_desc": request.POST.get("dep_desc"),
            "dep_div_code": request.POST.get("dep_div_code"),
            "dep_active": request.POST.get("dep_active"),
        }

        imported = 0
        updated = 0
        skipped = 0

        for row in range(2, sheet.max_row + 1):
            try:
                def get_value(db_field):
                    excel_col = mapping.get(db_field)
                    if not excel_col or excel_col not in headers:
                        return None

                    col_index = headers.index(excel_col) + 1
                    value = sheet.cell(row=row, column=col_index).value

                    if value is None:
                        return None

                    return str(value).strip()

                dep_code = get_value("dep_code")
                dep_desc = get_value("dep_desc")
                div_code = get_value("dep_div_code")
                dep_active_value = get_value("dep_active")

                if not dep_code or not dep_desc or not div_code:
                    skipped += 1
                    continue

                division = sys_div_master.objects.filter(div_code=div_code).first()

                if not division:
                    skipped += 1
                    continue

                dep_active = True
                if dep_active_value:
                    dep_active = dep_active_value.lower() in ["true", "1", "yes", "y", "active"]

                obj, created = sys_dep_master.objects.update_or_create(
                    dep_code=dep_code,
                    defaults={
                        "dep_desc": dep_desc,
                        "dep_div_code": division,
                        "dep_active": dep_active,
                    }
                )

                if created:
                    imported += 1
                else:
                    updated += 1

            except Exception:
                skipped += 1

        messages.success(
            request,
            f"Department import completed. Imported: {imported}, Updated: {updated}, Skipped: {skipped}"
        )

        return redirect("department_master_list")

    return redirect("department_master_list")


# employee views 
def employee_master_list(request):
    employees = (
        sys_emp_master.objects
        .select_related("emp_cmp", "emp_bra_code", "emp_dep_code")
        .all()
        .order_by("id")
    )

    companies = sys_cmp_master.objects.filter(cmp_active=True).order_by("cmp_desc")
    branches = sys_bra_master.objects.filter(bra_active=True).order_by("bra_desc")
    departments = sys_dep_master.objects.filter(dep_active=True).order_by("dep_desc")

    return render(request, "masters/employee_list.html", {
        "employees": employees,
        "companies": companies,
        "branches": branches,
        "departments": departments,
    })


def employee_master_create(request):
    if request.method == "POST":
        form = EmployeeMasterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee added successfully.")
        else:
            messages.error(request, "Employee could not be added.")

    return redirect("employee_master_list")


def employee_master_update(request, pk):
    employee = get_object_or_404(sys_emp_master, pk=pk)

    if request.method == "POST":
        form = EmployeeMasterForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee updated successfully.")
        else:
            messages.error(request, "Employee could not be updated.")

    return redirect("employee_master_list")


def employee_master_delete(request, pk):
    employee = get_object_or_404(sys_emp_master, pk=pk)

    if request.method == "POST":
        employee.delete()
        messages.success(request, "Employee deleted successfully.")

    return redirect("employee_master_list")



def employee_import_upload(request):
    if request.method == "POST":
        excel_file = request.FILES.get("excel_file")

        if not excel_file:
            messages.error(request, "Please upload an Excel file.")
            return redirect("employee_master_list")

        upload_dir = os.path.join(settings.MEDIA_ROOT, "imports")
        os.makedirs(upload_dir, exist_ok=True)

        file_name = f"{uuid.uuid4()}_{excel_file.name}"
        file_path = os.path.join(upload_dir, file_name)

        with open(file_path, "wb+") as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)

        workbook = load_workbook(file_path)
        sheet = workbook.active

        excel_columns = [
            str(cell.value).strip()
            for cell in sheet[1]
            if cell.value
        ]

        request.session["employee_import_file"] = file_path

        return render(request, "masters/employee_import_map.html", {
            "excel_columns": excel_columns,
            "db_fields": [
                ("emp_cmp", "Company Code"),
                ("emp_bra_code", "Branch Code"),
                ("emp_pno", "Employee PNO"),
                ("emp_name", "Employee Name"),
                ("emp_designation", "Designation"),
                ("emp_dep_code", "Department Code"),
                ("emp_email", "Email"),
                ("emp_mobile", "Mobile"),
                ("emp_phone", "Phone"),
                ("emp_pbx", "PBX"),
                ("emp_active", "Active"),
            ],
        })

    return redirect("employee_master_list")


def employee_import_process(request):
    if request.method == "POST":
        file_path = request.session.get("employee_import_file")

        if not file_path or not os.path.exists(file_path):
            messages.error(request, "Import file not found. Please upload again.")
            return redirect("employee_master_list")

        workbook = load_workbook(file_path)
        sheet = workbook.active

        headers = [
            str(cell.value).strip() if cell.value else ""
            for cell in sheet[1]
        ]

        mapping = {
            "emp_cmp": request.POST.get("emp_cmp"),
            "emp_bra_code": request.POST.get("emp_bra_code"),
            "emp_pno": request.POST.get("emp_pno"),
            "emp_name": request.POST.get("emp_name"),
            "emp_designation": request.POST.get("emp_designation"),
            "emp_dep_code": request.POST.get("emp_dep_code"),
            "emp_email": request.POST.get("emp_email"),
            "emp_mobile": request.POST.get("emp_mobile"),
            "emp_phone": request.POST.get("emp_phone"),
            "emp_pbx": request.POST.get("emp_pbx"),
            "emp_active": request.POST.get("emp_active"),
        }

        imported = 0
        updated = 0
        skipped = 0

        def get_value(row, db_field):
            excel_col = mapping.get(db_field)

            if not excel_col or excel_col not in headers:
                return None

            col_index = headers.index(excel_col) + 1
            value = sheet.cell(row=row, column=col_index).value

            if value is None:
                return None
            
            if isinstance(value, float) and value.is_integer():
                value = int(value)

            return str(value).strip()

        for row in range(2, sheet.max_row + 1):
            try:
                cmp_code = get_value(row, "emp_cmp")
                bra_code = get_value(row, "emp_bra_code")
                emp_pno = get_value(row, "emp_pno")
                emp_name = get_value(row, "emp_name")
                emp_designation = get_value(row, "emp_designation")
                dep_code = get_value(row, "emp_dep_code")

                if not cmp_code or not bra_code or not emp_pno or not emp_name or not dep_code:
                    skipped += 1
                    continue

                company = sys_cmp_master.objects.filter(cmp_code=cmp_code).first()
                branch = sys_bra_master.objects.filter(bra_code=bra_code).first()
                department = sys_dep_master.objects.filter(dep_code=dep_code).first()

                if not company or not branch or not department:
                    skipped += 1
                    continue

                emp_active_value = get_value(row, "emp_active")
                emp_active = True

                if emp_active_value:
                    emp_active = emp_active_value.lower() in ["true", "1", "yes", "y", "active"]

                obj, created = sys_emp_master.objects.update_or_create(
                    emp_pno=emp_pno,
                    defaults={
                        "emp_cmp": company,
                        "emp_bra_code": branch,
                        "emp_name": emp_name,
                        "emp_designation": emp_designation or "",
                        "emp_dep_code": department,
                        "emp_email": get_value(row, "emp_email"),
                        "emp_mobile": get_value(row, "emp_mobile"),
                        "emp_phone": get_value(row, "emp_phone"),
                        "emp_pbx": get_value(row, "emp_pbx"),
                        "emp_active": emp_active,
                    }
                )

                if created:
                    imported += 1
                else:
                    updated += 1

            except Exception:
                skipped += 1

        messages.success(
            request,
            f"Employee import completed. Imported: {imported}, Updated: {updated}, Skipped: {skipped}"
        )

        return redirect("employee_master_list")

    return redirect("employee_master_list")

# purpose views
def purpose_list(request):
    purposes = sys_pur_master.objects.all().order_by("pur_id")

    return render(request, "masters/purpose_list.html", {
        "purposes": purposes,
    })


def purpose_create(request):
    if request.method == "POST":
        form = PurposeMasterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Purpose added successfully.")
        else:
            messages.error(request, "Purpose could not be added.")

    return redirect("purpose_list")


def purpose_update(request, pk):
    purpose = get_object_or_404(sys_pur_master, pk=pk)

    if request.method == "POST":
        form = PurposeMasterForm(request.POST, instance=purpose)
        if form.is_valid():
            form.save()
            messages.success(request, "Purpose updated successfully.")
        else:
            messages.error(request, "Purpose could not be updated.")

    return redirect("purpose_list")


def purpose_delete(request, pk):
    purpose = get_object_or_404(sys_pur_master, pk=pk)

    if request.method == "POST":
        purpose.delete()
        messages.success(request, "Purpose deleted successfully.")

    return redirect("purpose_list")

# user views


def fetch_employee_details(request, emp_pno):
    employee = sys_emp_master.objects.filter(emp_pno=emp_pno).first()

    if not employee:
        return JsonResponse({
            "success": False,
            "message": "Employee not found."
        })

    full_name = employee.emp_name or ""
    name_parts = full_name.strip().split(" ", 1)

    first_name = name_parts[0] if len(name_parts) > 0 else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    return JsonResponse({
        "success": True,
        "first_name": first_name,
        "last_name": last_name,
        "designation": employee.emp_designation or "",
        "department": employee.emp_dep_code.dep_code if employee.emp_dep_code else "",
        "branch": employee.emp_bra_code.bra_code if employee.emp_bra_code else "",
        "company": employee.emp_cmp.cmp_code if employee.emp_cmp else "",
        "mobile": employee.emp_mobile or "",
        "email": employee.emp_email or "",
        "phone": employee.emp_phone or "",
    })


def sync_django_auth_user(user_obj, first_name, last_name, raw_password=None):
    django_user, created = User.objects.get_or_create(
        username=user_obj.usr_loginID,
        defaults={
            "email": user_obj.usr_email,
            "first_name": first_name,
            "last_name": last_name,
            "is_active": True,
        }
    )

    django_user.email = user_obj.usr_email
    django_user.first_name = first_name
    django_user.last_name = last_name
    django_user.is_active = True

    if user_obj.usr_auth == "LOCAL_DB":
        if raw_password:
            django_user.set_password(raw_password)
    else:
        django_user.set_unusable_password()

    django_user.groups.clear()

    if user_obj.usr_access_group:
        group = Group.objects.filter(id=user_obj.usr_access_group).first()
        if group:
            django_user.groups.add(group)

    django_user.save()


def user_master_list(request):
    users = sys_usr_system.objects.all().order_by("-id")

    departments = sys_dep_master.objects.all().order_by("dep_code")
    branches = sys_bra_master.objects.all().order_by("bra_code")
    companies = sys_cmp_master.objects.all().order_by("cmp_code")
    access_groups = Group.objects.all().order_by("name")

    return render(request, "masters/user_master_list.html", {
        "users": users,
        "departments": departments,
        "branches": branches,
        "companies": companies,
        "access_groups": access_groups,
    })


def user_master_create(request):
    departments = sys_dep_master.objects.all().order_by("dep_code")
    branches = sys_bra_master.objects.all().order_by("bra_code")
    companies = sys_cmp_master.objects.all().order_by("cmp_code")
    access_groups = Group.objects.all().order_by("name")

    if request.method == "POST":
        auth_type = request.POST.get("auth_type")
        password = request.POST.get("password")

        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        full_name = f"{first_name} {last_name}".strip()

        department = get_object_or_404(sys_dep_master, dep_code=request.POST.get("department"))
        branch = get_object_or_404(sys_bra_master, bra_code=request.POST.get("branch"))
        company = get_object_or_404(sys_cmp_master, cmp_code=request.POST.get("company"))

        user = sys_usr_system(
            usr_pno=request.POST.get("employee_id") or request.POST.get("login_id"),
            usr_name=full_name,
            usr_designation=request.POST.get("designation"),
            usr_dep_code=department,
            usr_mobile=request.POST.get("mobile"),
            usr_email=request.POST.get("email"),
            usr_phone=request.POST.get("phone"),
            usr_loginID=request.POST.get("login_id"),
            usr_auth=auth_type,
            usr_access_group=request.POST.get("access_group"),
            usr_bra_code=branch,
            usr_company=company,
        )

        if auth_type == "LOCAL_DB" and password:
            user.usr_password = make_password(password)

        if auth_type == "SSO":
            user.usr_password = None

        user.save()
        sync_django_auth_user(user, first_name, last_name, password)

        messages.success(request, "User created successfully.")
        return redirect("user_master_list")

    return render(request, "masters/user_master_form.html", {
        "departments": departments,
        "branches": branches,
        "companies": companies,
        "access_groups": access_groups,
        "user_obj": None,
    })


def user_master_update(request, pk):
    user_obj = get_object_or_404(sys_usr_system, pk=pk)

    departments = sys_dep_master.objects.all().order_by("dep_code")
    branches = sys_bra_master.objects.all().order_by("bra_code")
    companies = sys_cmp_master.objects.all().order_by("cmp_code")
    access_groups = Group.objects.all().order_by("name")

    if request.method == "POST":
        auth_type = request.POST.get("auth_type")
        password = request.POST.get("password")

        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        full_name = f"{first_name} {last_name}".strip()

        department = get_object_or_404(sys_dep_master, dep_code=request.POST.get("department"))
        branch = get_object_or_404(sys_bra_master, bra_code=request.POST.get("branch"))
        company = get_object_or_404(sys_cmp_master, cmp_code=request.POST.get("company"))

        user_obj.usr_pno = request.POST.get("employee_id") or request.POST.get("login_id")
        user_obj.usr_name = full_name
        user_obj.usr_designation = request.POST.get("designation")
        user_obj.usr_dep_code = department
        user_obj.usr_mobile = request.POST.get("mobile")
        user_obj.usr_email = request.POST.get("email")
        user_obj.usr_phone = request.POST.get("phone")
        user_obj.usr_loginID = request.POST.get("login_id")
        user_obj.usr_auth = auth_type
        user_obj.usr_access_group = request.POST.get("access_group")
        user_obj.usr_bra_code = branch
        user_obj.usr_company = company

        if auth_type == "LOCAL_DB" and password:
            user_obj.usr_password = make_password(password)

        if auth_type == "SSO":
            user_obj.usr_password = None

        user_obj.save()
        sync_django_auth_user(user_obj, first_name, last_name, password)

        messages.success(request, "User updated successfully.")
        return redirect("user_master_list")

    full_name = user_obj.usr_name or ""
    name_parts = full_name.strip().split(" ", 1)

    user_obj.first_name_display = name_parts[0] if len(name_parts) > 0 else ""
    user_obj.last_name_display = name_parts[1] if len(name_parts) > 1 else ""

    return render(request, "masters/user_master_form.html", {
        "departments": departments,
        "branches": branches,
        "companies": companies,
        "access_groups": access_groups,
        "user_obj": user_obj,
    })


def user_master_delete(request, pk):
    user_obj = get_object_or_404(sys_usr_system, pk=pk)

    if request.method == "POST":
        User.objects.filter(username=user_obj.usr_loginID).delete()
        user_obj.delete()
        messages.success(request, "User deleted successfully.")

    return redirect("user_master_list")