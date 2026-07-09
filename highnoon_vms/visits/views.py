from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required

from .models import visit
from visitors.models import visitor, visitor_card
from masters.models import sys_emp_master, sys_pur_master


@login_required
@permission_required("visits.view_visit", raise_exception=True)
def visit_list(request):
    search = request.GET.get("search", "")
    today = timezone.localdate()

    start_of_day = timezone.make_aware(
        timezone.datetime.combine(today, timezone.datetime.min.time())
    )

    end_of_day = timezone.make_aware(
        timezone.datetime.combine(today, timezone.datetime.max.time())
    )

    visits = visit.objects.filter(
        Q(check_in_time__range=(start_of_day, end_of_day)) |
        Q(status="Checked In")
    ).order_by("-check_in_time")

    if search:
        visits = visits.filter(
            visitor_card__CRD_No__icontains=search
        )

    visitors = visitor.objects.all().order_by("visitor_name")
    employees = sys_emp_master.objects.all().order_by("emp_name")
    cards = visitor_card.objects.filter(CRD_Active=True).order_by("CRD_No")
    purposes = sys_pur_master.objects.filter(
        pur_active=True
    ).order_by("pur_purpose")

    return render(request, "visits/visit_list.html", {
        "visits": visits,
        "visitors": visitors,
        "employees": employees,
        "cards": cards,
        "purposes": purposes,
        "search": search,
        "today": today,
        "selected_visitor_id": request.GET.get("visitor_id"),
        "open_add_visit": request.GET.get("open_add_visit"),
    })


@login_required
@permission_required("visits.change_visit", raise_exception=True)
def visit_checkout(request, visit_id):
    visit_obj = get_object_or_404(visit, visit_id=visit_id)

    if request.method == "POST":
        visit_obj.check_out_time = timezone.now()
        visit_obj.status = "Checked Out"

        if visit_obj.visitor_card:
            visit_obj.visitor_card.CRD_Active = True
            visit_obj.visitor_card.save()

        visit_obj.save()

        messages.success(request, "Visitor checked out successfully.")

    return redirect("visit_list")


@login_required
@permission_required("visits.add_visit", raise_exception=True)
def visit_create(request):

    if request.method == "POST":

        visitor_obj = get_object_or_404(
            visitor,
            visitor_id=request.POST.get("visitor")
        )

        employee_obj = get_object_or_404(
            sys_emp_master,
            pk=request.POST.get("employee")
        )

        selected_card = get_object_or_404(
            visitor_card,
            id=request.POST.get("visitor_card")
        )

        if not selected_card.CRD_Active:
            messages.error(
                request,
                f"Card {selected_card.CRD_No} is currently unavailable."
            )
            return redirect("visit_list")

        card_in_use = visit.objects.filter(
            visitor_card=selected_card,
            status="Checked In"
        ).exists()

        if card_in_use:
            messages.error(
                request,
                f"Card {selected_card.CRD_No} is already in use."
            )
            return redirect("visit_list")

        purpose_obj = get_object_or_404(
            sys_pur_master,
            pur_id=request.POST.get("purpose")
        )

        if purpose_obj.pur_purpose.lower() in ["other", "others"]:

            visit_purpose = request.POST.get(
                "other_purpose",
                ""
            ).strip()

            if not visit_purpose:
                messages.error(
                    request,
                    "Please specify the purpose."
                )
                return redirect("visit_list")

        else:
            visit_purpose = purpose_obj.pur_purpose

        visit.objects.create(
            visitor=visitor_obj,
            employee=employee_obj,
            visitor_card=selected_card,
            visit_purpose=visit_purpose,
        )

        selected_card.CRD_Active = False
        selected_card.save()

        messages.success(request, "Visit created successfully.")

    return redirect("visit_list")