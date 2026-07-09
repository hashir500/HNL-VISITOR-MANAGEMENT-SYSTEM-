from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth.decorators import login_required, permission_required

from visits.models import visit
from visitors.models import visitor, visitor_card
from masters.models import sys_emp_master, sys_dep_master


@login_required
@permission_required("dashboard.view_dashboard", raise_exception=True)
def dashboard_page(request):
    today = timezone.localdate()

    start_of_day = timezone.make_aware(
        timezone.datetime.combine(today, timezone.datetime.min.time())
    )

    end_of_day = timezone.make_aware(
        timezone.datetime.combine(today, timezone.datetime.max.time())
    )

    today_visits = visit.objects.filter(
        check_in_time__range=(start_of_day, end_of_day)
    )

    active_visits = visit.objects.filter(status="Checked In")

    checked_out_today = visit.objects.filter(
        check_out_time__range=(start_of_day, end_of_day),
        status="Checked Out"
    )

    total_visitors = visitor.objects.count()
    total_employees = sys_emp_master.objects.count()
    total_departments = sys_dep_master.objects.count()

    total_cards = visitor_card.objects.count()
    available_cards = visitor_card.objects.filter(CRD_Active=True).count()

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

    department_usage = (
        visit.objects
        .filter(employee__isnull=False)
        .values("employee__emp_dep_code__dep_desc")
        .annotate(total=Count("visit_id"))
        .order_by("-total")[:5]
    )

    department_labels = [
        item["employee__emp_dep_code__dep_desc"] or "Unknown"
        for item in department_usage
    ]

    department_counts = [
        item["total"]
        for item in department_usage
    ]

    return render(request, "dashboard/dashboard_page.html", {
        "today_visits_count": today_visits.count(),
        "active_visits_count": active_visits.count(),
        "checked_out_today_count": checked_out_today.count(),

        "available_cards_count": available_cards,
        "total_cards_count": total_cards,

        "total_visitors": total_visitors,
        "total_employees": total_employees,
        "total_departments": total_departments,

        "recent_visits": recent_visits,
        "active_visitors": active_visitors,

        "today": today,

        "last_7_days_labels": last_7_days_labels,
        "last_7_days_counts": last_7_days_counts,

        "department_labels": department_labels,
        "department_counts": department_counts,
    })