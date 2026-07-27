from datetime import timedelta
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.dateparse import parse_date

from visits.models import visit
from visitors.models import visitor, visitor_card
from masters.models import sys_emp_master, sys_dep_master


@login_required
@permission_required("dashboard.view_dashboard", raise_exception=True)
def dashboard_page(request):
    today = timezone.localdate()

    period = request.GET.get("period", "daily").lower()
    start_date_str = request.GET.get("start_date", "")
    end_date_str = request.GET.get("end_date", "")

    # Handle Filter Date Ranges
    if period == "custom" and start_date_str and end_date_str:
        s_date = parse_date(start_date_str) or today
        e_date = parse_date(end_date_str) or today
    elif period == "weekly":
        s_date = today - timedelta(days=7)
        e_date = today
    elif period == "monthly":
        s_date = today - timedelta(days=30)
        e_date = today
    elif period == "quarterly":
        s_date = today - timedelta(days=90)
        e_date = today
    elif period == "yearly":
        s_date = today - timedelta(days=365)
        e_date = today
    else:  # 'daily' or default
        period = "daily"
        s_date = today
        e_date = today

    start_datetime = timezone.make_aware(
        timezone.datetime.combine(s_date, timezone.datetime.min.time())
    )
    end_datetime = timezone.make_aware(
        timezone.datetime.combine(e_date, timezone.datetime.max.time())
    )

    # Filtered Base Queryset
    filtered_visits = visit.objects.filter(
        check_in_time__range=(start_datetime, end_datetime)
    )

    today_visits_count = filtered_visits.count()
    active_visits = visit.objects.filter(status="Checked In")

    # Count Unique Visitors in Period
    unique_visitors_count = filtered_visits.values("visitor_id").distinct().count()

    recent_visits = filtered_visits.order_by("-check_in_time")[:5]
    active_visitors = active_visits.order_by("-check_in_time")[:5]

    # Dynamic Line Chart Trend Generation
    chart_labels = []
    chart_counts = []

    num_days = (e_date - s_date).days
    if num_days <= 0:
        num_days = 1

    step = max(1, num_days // 10)  # max ~10 points on chart
    curr_date = s_date

    while curr_date <= e_date:
        next_date = min(curr_date + timedelta(days=step - 1), e_date)
        
        if curr_date == next_date:
            label = curr_date.strftime("%d %b")
            cnt = visit.objects.filter(check_in_time__date=curr_date).count()
        else:
            label = f"{curr_date.strftime('%d %b')} - {next_date.strftime('%d %b')}"
            c_start = timezone.make_aware(timezone.datetime.combine(curr_date, timezone.datetime.min.time()))
            c_end = timezone.make_aware(timezone.datetime.combine(next_date, timezone.datetime.max.time()))
            cnt = visit.objects.filter(check_in_time__range=(c_start, c_end)).count()

        chart_labels.append(label)
        chart_counts.append(cnt)
        curr_date = next_date + timedelta(days=1)

    # Department Usage Annotations
    department_usage = (
        filtered_visits.filter(employee__isnull=False)
        .values("employee__emp_dep_code__dep_desc")
        .annotate(total=Count("visit_id"))
        .order_by("-total")[:5]
    )

    department_labels = [
        item["employee__emp_dep_code__dep_desc"] or "Unknown"
        for item in department_usage
    ]

    department_counts = [item["total"] for item in department_usage]

    return render(
        request,
        "dashboard/dashboard_page.html",
        {
            "today_visits_count": today_visits_count,
            "active_visits_count": active_visits.count(),
            "unique_visitors_count": unique_visitors_count,
            "recent_visits": recent_visits,
            "active_visitors": active_visitors,
            "today": today,
            "period": period,
            "start_date": s_date.strftime("%Y-%m-%d"),
            "end_date": e_date.strftime("%Y-%m-%d"),
            "chart_labels": chart_labels,
            "chart_counts": chart_counts,
            "department_labels": department_labels,
            "department_counts": department_counts,
        },
    )