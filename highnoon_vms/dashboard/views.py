from collections import defaultdict
from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count

from visits.models import visit
from visitors.models import visitor, visitor_card
from employees.models import employee, department
from django.contrib.auth.decorators import login_required, permission_required


@login_required
@permission_required("dashboard.view_dashboard", raise_exception=True)
def dashboard_page(request):
    today = timezone.localdate()

    today_visits = visit.objects.filter(check_in_time__date=today)
    active_visits = visit.objects.filter(status="Checked In")
    checked_out_today = today_visits.filter(status="Checked Out")

    total_visitors = visitor.objects.count()
    total_employees = employee.objects.count()
    total_departments = department.objects.count()

    available_cards = visitor_card.objects.filter(is_available=True).count()
    cards_in_use = visitor_card.objects.filter(is_available=False).count()

    recent_visits = visit.objects.all().order_by("-check_in_time")[:5]
    active_visitors = active_visits.order_by("-check_in_time")[:5]

    last_7_days_labels = []
    last_7_days_counts = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        last_7_days_labels.append(day.strftime("%d %b"))
        last_7_days_counts.append(
            visit.objects.filter(check_in_time__date=day).count()
        )

    usage = defaultdict(int)

    card_usage = (
        visit.objects
        .filter(visitor_card__isnull=False)
        .values("visitor_card__card_color")
        .annotate(total=Count("visit_id"))
    )

    for item in card_usage:
        usage[item["visitor_card__card_color"]] = item["total"]

    card_color_labels = ["Red", "Blue", "Green"]
    card_color_counts = [
        usage["Red"],
        usage["Blue"],
        usage["Green"],
    ]

    return render(request, "dashboard/dashboard_page.html", {
        "today_visits_count": today_visits.count(),
        "active_visits_count": active_visits.count(),
        "checked_out_today_count": checked_out_today.count(),
        "available_cards_count": available_cards,
        "cards_in_use_count": cards_in_use,
        "total_visitors": total_visitors,
        "total_employees": total_employees,
        "total_departments": total_departments,
        "recent_visits": recent_visits,
        "active_visitors": active_visitors,
        "today": today,
        "last_7_days_labels": last_7_days_labels,
        "last_7_days_counts": last_7_days_counts,
        "card_color_labels": card_color_labels,
        "card_color_counts": card_color_counts,
    })