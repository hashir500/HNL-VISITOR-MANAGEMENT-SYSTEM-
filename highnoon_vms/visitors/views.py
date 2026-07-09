from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse
from openpyxl import load_workbook
from django.contrib import messages
from .models import visitor_card, visitor
import os
from django.conf import settings


@login_required
@permission_required("visitors.view_visitor_card", raise_exception=True)
def visitor_card_list(request):
    cards = visitor_card.objects.all().order_by("id")

    return render(request, "visitors/visitor_card_list.html", {
        "cards": cards,
    })


@login_required
@permission_required("visitors.add_visitor_card", raise_exception=True)
def visitor_card_create(request):
    if request.method == "POST":
        crd_no = request.POST.get("CRD_No", "").strip()
        crd_desc = request.POST.get("CRD_Desc", "").strip()
        crd_active = True if request.POST.get("CRD_Active") else False

        if visitor_card.objects.filter(CRD_No__iexact=crd_no).exists():
            messages.error(request, f"Card number {crd_no} already exists.")
            return redirect("visitor_card_list")

        visitor_card.objects.create(
            CRD_No=crd_no,
            CRD_Desc=crd_desc,
            CRD_Active=crd_active,
        )

        messages.success(request, "Visitor card created successfully.")

    return redirect("visitor_card_list")


@login_required
@permission_required("visitors.change_visitor_card", raise_exception=True)
def visitor_card_update(request, pk):
    card = get_object_or_404(visitor_card, pk=pk)

    if request.method == "POST":
        crd_no = request.POST.get("CRD_No", "").strip()
        crd_desc = request.POST.get("CRD_Desc", "").strip()
        crd_active = True if request.POST.get("CRD_Active") else False

        if visitor_card.objects.filter(CRD_No__iexact=crd_no).exclude(pk=pk).exists():
            messages.error(request, f"Card number {crd_no} already exists.")
            return redirect("visitor_card_list")

        card.CRD_No = crd_no
        card.CRD_Desc = crd_desc
        card.CRD_Active = crd_active
        card.save()

        messages.success(request, "Visitor card updated successfully.")

    return redirect("visitor_card_list")


@login_required
@permission_required("visitors.delete_visitor_card", raise_exception=True)
def visitor_card_delete(request, pk):
    card = get_object_or_404(visitor_card, pk=pk)

    if request.method == "POST":
        card.delete()
        messages.success(request, "Visitor card deleted successfully.")

    return redirect("visitor_card_list")

# visitor views
@login_required
@permission_required("visitors.view_visitor", raise_exception=True)
def visitor_list(request):
    visitors = visitor.objects.all()

    return render(request, "visitors/visitor_list.html", {
        "visitors": visitors,
    })


@login_required
@permission_required("visitors.add_visitor", raise_exception=True)
def visitor_create(request):
    if request.method == "POST":
        new_visitor = visitor.objects.create(
            visitor_name=request.POST.get("visitor_name"),
            visitor_email=request.POST.get("visitor_email") or None,
            visitor_phone=request.POST.get("visitor_phone"),
            visitor_address=request.POST.get("visitor_address") or None,
        )

        next_page = request.POST.get("next")

        if next_page == "visits":
            return redirect(
                f"{reverse('visit_list')}?open_add_visit=1&visitor_id={new_visitor.visitor_id}"
            )

    return redirect("visitor_list")


@login_required
@permission_required("visitors.change_visitor", raise_exception=True)
def visitor_update(request, visitor_id):
    v = get_object_or_404(visitor, visitor_id=visitor_id)

    if request.method == "POST":
        v.visitor_name = request.POST.get("visitor_name")
        v.visitor_email = request.POST.get("visitor_email") or None
        v.visitor_phone = request.POST.get("visitor_phone")
        v.visitor_address = request.POST.get("visitor_address") or None
        v.save()

    return redirect("visitor_list")


@login_required
@permission_required("visitors.delete_visitor", raise_exception=True)
def visitor_delete(request, visitor_id):
    v = get_object_or_404(visitor, visitor_id=visitor_id)

    if request.method == "POST":
        v.delete()

    return redirect("visitor_list")



# visitor card import
@login_required
@permission_required("visitors.add_visitor_card", raise_exception=True)
def visitor_card_import_upload(request):
    if request.method == "POST":
        excel_file = request.FILES.get("excel_file")

        if not excel_file:
            messages.error(request, "Please upload an Excel file.")
            return redirect("visitor_card_list")

        upload_dir = os.path.join(settings.MEDIA_ROOT, "imports")
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, excel_file.name)

        with open(file_path, "wb+") as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)

        workbook = load_workbook(file_path)
        sheet = workbook.active

        headers = [
            str(cell.value).strip() if cell.value else ""
            for cell in sheet[1]
        ]

        request.session["visitor_card_import_file"] = file_path
        request.session["visitor_card_import_headers"] = headers

        return render(request, "visitors/visitor_card_import_mapping.html", {
            "headers": headers,
        })

    return redirect("visitor_card_list")


@login_required
@permission_required("visitors.add_visitor_card", raise_exception=True)
def visitor_card_import_process(request):
    if request.method == "POST":
        file_path = request.session.get("visitor_card_import_file")

        if not file_path or not os.path.exists(file_path):
            messages.error(request, "Import file not found. Please upload again.")
            return redirect("visitor_card_list")

        workbook = load_workbook(file_path)
        sheet = workbook.active

        headers = [
            str(cell.value).strip() if cell.value else ""
            for cell in sheet[1]
        ]

        mapping = {
            "CRD_No": request.POST.get("CRD_No"),
            "CRD_Desc": request.POST.get("CRD_Desc"),
            "CRD_Active": request.POST.get("CRD_Active"),
        }

        def get_value(row, field):
            excel_col = mapping.get(field)

            if not excel_col or excel_col not in headers:
                return None

            col_index = headers.index(excel_col) + 1
            value = sheet.cell(row=row, column=col_index).value

            if value is None:
                return None

            if isinstance(value, (int, float)):
                if float(value).is_integer():
                    return str(int(value))
                return str(value)

            return str(value).strip()

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for row in range(2, sheet.max_row + 1):
            crd_no = get_value(row, "CRD_No")
            crd_desc = get_value(row, "CRD_Desc")
            crd_active = get_value(row, "CRD_Active")

            if not crd_no:
                skipped_count += 1
                continue

            active_text = str(crd_active).strip().lower() if crd_active else "true"

            is_active = active_text in [
                "true",
                "1",
                "yes",
                "y",
                "active",
            ]

            card, created = visitor_card.objects.update_or_create(
                CRD_No=crd_no,
                defaults={
                    "CRD_Desc": crd_desc or "",
                    "CRD_Active": is_active,
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        request.session.pop("visitor_card_import_file", None)
        request.session.pop("visitor_card_import_headers", None)

        messages.success(
            request,
            f"Import completed. Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}."
        )

    return redirect("visitor_card_list")


@login_required
@permission_required("visitors.delete_visitor_card", raise_exception=True)
def visitor_card_delete_all(request):
    if request.method == "POST":
        visitor_card.objects.all().delete()
        messages.success(request, "All visitor cards deleted successfully.")

    return redirect("visitor_card_list")