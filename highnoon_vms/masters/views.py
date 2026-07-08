from django.shortcuts import render, redirect, get_object_or_404

from .models import sys_cmp_master
from .forms import CompanyMasterForm
from .models import sys_bra_master
from .forms import BranchMasterForm
from .models import sys_div_master
from .forms import DivisionMasterForm

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