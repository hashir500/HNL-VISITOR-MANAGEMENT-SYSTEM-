from django.shortcuts import redirect, get_object_or_404,render
from django.utils import timezone
from django.contrib import messages

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
        "selected_visitor_id": request.GET.get("visitor_id"),
        "open_add_visit": request.GET.get("open_add_visit"),
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
        visitor_obj = get_object_or_404(visitor, visitor_id=request.POST.get("visitor"))
        employee_obj = get_object_or_404(employee, employee_id=request.POST.get("employee"))

        card_color = request.POST.get("card_color")
        card_number = request.POST.get("card_number")

        selected_card = visitor_card.objects.filter(
            card_color=card_color,
            card_number=card_number,
            is_available=True
        ).first()

        if selected_card is None:
            messages.error(request, f"Card {card_number} ({card_color}) is already assigned or does not exist.")
            return redirect("visit_list")

        visit.objects.create(
            visitor=visitor_obj,
            employee=employee_obj,
            visitor_card=selected_card,
            visit_purpose=request.POST.get("visit_purpose"),
        )

        selected_card.is_available = False
        selected_card.save()

        messages.success(request, "Visit created successfully.")

    return redirect("visit_list")