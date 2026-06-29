from django.shortcuts import redirect, get_object_or_404,render
from django.utils import timezone

from .models import visit
from visitors.models import visitor, visitor_card
from employees.models import employee


def visit_list(request):
    visits = visit.objects.all().order_by("-check_in_time")
    visitors = visitor.objects.all()
    employees = employee.objects.all()
    cards = visitor_card.objects.all()

    return render(request, "visits/visit_list.html", {
        "visits": visits,
        "visitors": visitors,
        "employees": employees,
        "cards": cards,
    })


def visit_checkout(request, visit_id):
    visit_obj = get_object_or_404(visit, visit_id=visit_id)

    if request.method == "POST":
        visit_obj.check_out_time = timezone.now()
        visit_obj.status = "Checked Out"

        if visit_obj.visitor_card:
            visit_obj.visitor_card.is_available = True
            visit_obj.visitor_card.save()

        visit_obj.save()

    return redirect("visit_list")



def visit_create(request):
    if request.method == "POST":

        visitor_obj = get_object_or_404(
            visitor,
            visitor_id=request.POST["visitor"]
        )

        employee_obj = get_object_or_404(
            employee,
            employee_id=request.POST["employee"]
        )

        available_card = visitor_card.objects.filter(
        card_color=request.POST.get("card_color"),
        is_available=True
        ).first()

        visit.objects.create(
            visitor=visitor_obj,
            employee=employee_obj,
            visitor_card=available_card,
            visit_purpose=request.POST["visit_purpose"],
        )

        if available_card:
            available_card.is_available = False
            available_card.save()

    return redirect("visit_list")