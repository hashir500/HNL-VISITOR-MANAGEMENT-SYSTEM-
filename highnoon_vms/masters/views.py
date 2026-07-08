from django.shortcuts import render, redirect, get_object_or_404
import requests
import openpyxl

from django.contrib import messages
from django.conf import settings
import os
import uuid
from openpyxl import load_workbook


from .models import sys_cmp_master
from .forms import CompanyMasterForm
from .models import sys_bra_master
from .forms import BranchMasterForm
from .models import sys_div_master
from .forms import DivisionMasterForm
from .models import sys_dep_master, sys_div_master
from .forms import DepartmentMasterForm

# company views
def company_list(request):
    companies = sys_cmp_master.objects.all().order_by("cmp_code")
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