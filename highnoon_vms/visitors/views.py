from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse

from .models import visitor_card, visitor


@login_required
@permission_required("visitors.view_visitor_card", raise_exception=True)
def visitor_card_list(request):
    cards = visitor_card.objects.all().order_by("CRD_No")

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