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

    selected_day = request.GET.get("selected_day", today.strftime("%Y-%m-%d"))
    selected_month = request.GET.get("selected_month", today.strftime("%Y-%m"))
    selected_week = request.GET.get("selected_week", f"{today.year}-W{today.isocalendar()[1]:02d}")
    selected_quarter_year = request.GET.get("selected_quarter_year", str(today.year))
    selected_quarter = request.GET.get("selected_quarter", str((today.month - 1) // 3 + 1))
    selected_year = request.GET.get("selected_year", str(today.year))

    start_date_str = request.GET.get("start_date", "")
    end_date_str = request.GET.get("end_date", "")

    # Calculate exact Start and End dates for each selection
    if period == "daily":
        s_date = parse_date(selected_day) or today
        e_date = s_date

    elif period == "weekly":
        try:
            yr, wk = map(int, selected_week.split("-W"))
            s_date = timezone.datetime.strptime(f"{yr}-W{wk}-1", "%G-W%V-%u").date()
            e_date = s_date + timedelta(days=6)
        except Exception:
            s_date = today - timedelta(days=7)
            e_date = today

    elif period == "monthly":
        try:
            yr, mn = map(int, selected_month.split("-"))
            s_date = timezone.datetime(yr, mn, 1).date()
            if mn == 12:
                next_m = timezone.datetime(yr + 1, 1, 1).date()
            else:
                next_m = timezone.datetime(yr, mn + 1, 1).date()
            e_date = next_m - timedelta(days=1)
        except Exception:
            s_date = today.replace(day=1)
            e_date = today

    elif period == "quarterly":
        try:
            yr = int(selected_quarter_year)
            qtr = int(selected_quarter)
            start_month = (qtr - 1) * 3 + 1
            s_date = timezone.datetime(yr, start_month, 1).date()
            end_month = start_month + 2
            if end_month == 12:
                next_m = timezone.datetime(yr + 1, 1, 1).date()
            else:
                next_m = timezone.datetime(yr, end_month + 1, 1).date()
            e_date = next_m - timedelta(days=1)
        except Exception:
            s_date = today - timedelta(days=90)
            e_date = today

    elif period == "yearly":
        try:
            yr = int(selected_year)
            s_date = timezone.datetime(yr, 1, 1).date()
            e_date = timezone.datetime(yr, 12, 31).date()
        except Exception:
            s_date = timezone.datetime(today.year, 1, 1).date()
            e_date = timezone.datetime(today.year, 12, 31).date()

    elif period == "custom" and start_date_str and end_date_str:
        s_date = parse_date(start_date_str) or today
        e_date = parse_date(end_date_str) or today
    else:
        period = "daily"
        s_date = today
        e_date = today

    start_datetime = timezone.make_aware(
        timezone.datetime.combine(s_date, timezone.datetime.min.time())
    )
    end_datetime = timezone.make_aware(
        timezone.datetime.combine(e_date, timezone.datetime.max.time())
    )

    # Filtered Visits Queryset
    filtered_visits = visit.objects.filter(
        check_in_time__range=(start_datetime, end_datetime)
    )

    today_visits_count = filtered_visits.count()
    active_visits = visit.objects.filter(status="Checked In")
    unique_visitors_count = filtered_visits.values("visitor_id").distinct().count()

    recent_visits = filtered_visits.order_by("-check_in_time")[:5]
    active_visitors = active_visits.order_by("-check_in_time")[:5]

    chart_labels = []
    chart_counts = []

    # HOURLY BREAKDOWN FOR DAILY VIEW
    if s_date == e_date:
        for hour in range(8, 20):  # 8:00 AM to 7:00 PM
            h_start = timezone.make_aware(
                timezone.datetime.combine(s_date, timezone.datetime.min.time().replace(hour=hour))
            )
            h_end = timezone.make_aware(
                timezone.datetime.combine(s_date, timezone.datetime.min.time().replace(hour=hour, minute=59, second=59))
            )

            label = h_start.strftime("%I:%M %p")
            if label.startswith("0"):
                label = label[1:]

            cnt = visit.objects.filter(check_in_time__range=(h_start, h_end)).count()

            chart_labels.append(label)
            chart_counts.append(cnt)
    else:
        num_days = (e_date - s_date).days
        step = max(1, num_days // 10)
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

    # TOP 5 DEPARTMENTS + "OTHERS" AGGREGATION
    top_5_departments = (
        filtered_visits.filter(employee__isnull=False)
        .values("employee__emp_dep_code__dep_desc")
        .annotate(total=Count("visit_id"))
        .order_by("-total")[:5]
    )

    department_labels = []
    department_counts = []

    for item in top_5_departments:
        dep_name = item["employee__emp_dep_code__dep_desc"] or "Unknown"
        department_labels.append(dep_name)
        department_counts.append(item["total"])

    top_5_names = [item["employee__emp_dep_code__dep_desc"] for item in top_5_departments]

    other_visits_count = (
        filtered_visits.filter(employee__isnull=False)
        .exclude(employee__emp_dep_code__dep_desc__in=top_5_names)
        .count()
    )

    if other_visits_count > 0:
        department_labels.append("Others")
        department_counts.append(other_visits_count)

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
            "selected_day": selected_day,
            "selected_month": selected_month,
            "selected_week": selected_week,
            "selected_quarter_year": selected_quarter_year,
            "selected_quarter": selected_quarter,
            "selected_year": selected_year,
            "start_date": s_date.strftime("%Y-%m-%d"),
            "end_date": e_date.strftime("%Y-%m-%d"),
            "chart_labels": chart_labels,
            "chart_counts": chart_counts,
            "department_labels": department_labels,
            "department_counts": department_counts,
        },
    )