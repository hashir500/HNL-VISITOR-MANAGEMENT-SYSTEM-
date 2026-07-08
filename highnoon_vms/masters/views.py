from django.shortcuts import render, redirect, get_object_or_404

from .models import sys_cmp_master
from .forms import CompanyMasterForm


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