from calendar import monthrange
from datetime import date, datetime, time, timedelta
from urllib.parse import urlencode
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import (
    Avg,
    Count,
    DurationField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
)
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone

from xhtml2pdf import pisa

from masters.models import (
    sys_bra_master,
    sys_cmp_master,
    sys_emp_master,
    sys_pur_master,
    sys_usr_system,
)
from visitors.models import visitor, visitor_card
from visits.models import visit


# =========================================================
# GENERAL HELPERS
# =========================================================

def normalize_filter_value(value):
    value = (value or "").strip()
    if not value or value.upper() == "ALL":
        return None
    return value


def safe_parse_date(value, default_value=None):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return default_value


def make_start_datetime(selected_date):
    return timezone.make_aware(datetime.combine(selected_date, time.min))


def make_end_datetime(selected_date):
    return timezone.make_aware(datetime.combine(selected_date, time.max))


def format_duration(duration_value):
    if not duration_value:
        return "-"

    total_seconds = int(duration_value.total_seconds())
    if total_seconds < 0:
        return "-"

    total_minutes = total_seconds // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60

    if hours and minutes:
        hour_label = "hr" if hours == 1 else "hrs"
        minute_label = "min" if minutes == 1 else "mins"
        return f"{hours} {hour_label} {minutes} {minute_label}"

    if hours:
        hour_label = "hr" if hours == 1 else "hrs"
        return f"{hours} {hour_label}"

    minute_label = "min" if total_minutes == 1 else "mins"
    return f"{total_minutes} {minute_label}"


# =========================================================
# ACCESS SETTINGS
# =========================================================

def get_logged_in_vms_user(request):
    if request.user.is_superuser:
        return None

    login_id = (request.user.username or request.user.email or "").strip().lower()
    return sys_usr_system.objects.select_related("usr_company", "usr_bra_code").filter(usr_loginID__iexact=login_id).first()


def get_report_access_settings(request):
    if request.user.is_superuser:
        return {
            "has_access": True,
            "user_master": None,
            "can_select_company": True,
            "can_select_branch": True,
            "assigned_company_code": None,
            "assigned_branch_code": None,
        }

    user_master = get_logged_in_vms_user(request)

    if not user_master:
        return {
            "has_access": False,
            "user_master": None,
            "can_select_company": False,
            "can_select_branch": False,
            "assigned_company_code": None,
            "assigned_branch_code": None,
        }

    return {
        "has_access": True,
        "user_master": user_master,
        "can_select_company": user_master.usr_company is None,
        "can_select_branch": user_master.usr_bra_code is None,
        "assigned_company_code": user_master.usr_company.cmp_code if user_master.usr_company else None,
        "assigned_branch_code": user_master.usr_bra_code.bra_code if user_master.usr_bra_code else None,
    }


def get_selected_company_branch(request, access):
    selected_company = normalize_filter_value(request.GET.get("company")) if access["can_select_company"] else access["assigned_company_code"]
    selected_branch = normalize_filter_value(request.GET.get("branch")) if access["can_select_branch"] else access["assigned_branch_code"]
    return selected_company, selected_branch


def apply_report_access_filter(queryset, access, selected_company=None, selected_branch=None):
    if not access["has_access"]:
        return queryset.none()

    if not access["can_select_company"]:
        selected_company = access["assigned_company_code"]

    if not access["can_select_branch"]:
        selected_branch = access["assigned_branch_code"]

    if selected_company:
        queryset = queryset.filter(employee__emp_cmp__cmp_code=selected_company)

    if selected_branch:
        queryset = queryset.filter(employee__emp_bra_code__bra_code=selected_branch)

    return queryset


def get_report_filter_options(access, selected_company=None, selected_branch=None):
    companies = sys_cmp_master.objects.all().order_by("cmp_code")
    branches = sys_bra_master.objects.all().order_by("bra_code")
    employees = sys_emp_master.objects.select_related("emp_cmp", "emp_bra_code", "emp_dep_code").filter(emp_active=True).order_by("emp_name")

    if not access["has_access"]:
        return {"companies": companies.none(), "branches": branches.none(), "employees": employees.none()}

    if not access["can_select_company"]:
        companies = companies.filter(cmp_code=access["assigned_company_code"])
        employees = employees.filter(emp_cmp__cmp_code=access["assigned_company_code"])
    elif selected_company:
        employees = employees.filter(emp_cmp__cmp_code=selected_company)

    if not access["can_select_branch"]:
        branches = branches.filter(bra_code=access["assigned_branch_code"])
        employees = employees.filter(emp_bra_code__bra_code=access["assigned_branch_code"])
    elif selected_branch:
        employees = employees.filter(emp_bra_code__bra_code=selected_branch)

    return {"companies": companies, "branches": branches, "employees": employees}


# =========================================================
# DATE FILTERS (Default: 1st of current month to Today)
# =========================================================

def get_report_date_range(request):
    today = timezone.localdate()
    default_start = today.replace(day=1)

    selected_start_date = request.GET.get("start_date") or default_start.strftime("%Y-%m-%d")
    selected_end_date = request.GET.get("end_date") or today.strftime("%Y-%m-%d")

    start_date = safe_parse_date(selected_start_date, default_start)
    end_date = safe_parse_date(selected_end_date, today)

    if end_date < start_date:
        start_date, end_date = end_date, start_date

    start_datetime = make_start_datetime(start_date)
    end_datetime = make_end_datetime(end_date)

    if start_date == end_date:
        title_suffix = start_date.strftime("%d %B %Y")
    else:
        title_suffix = f"{start_date.strftime('%d %B %Y')} to {end_date.strftime('%d %B %Y')}"

    return {
        "report_type": request.GET.get("report_type", "custom"),
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "title_suffix": title_suffix,
        "selected_start_date": selected_start_date,
        "selected_end_date": selected_end_date,
        "start_date_obj": start_date,
        "end_date_obj": end_date,
    }


def apply_date_filter(queryset, date_settings):
    start_datetime = date_settings["start_datetime"]
    end_datetime = date_settings["end_datetime"]

    if start_datetime and end_datetime:
        queryset = queryset.filter(check_in_time__range=(start_datetime, end_datetime))
    return queryset


# =========================================================
# SHARED QUERYSETS
# =========================================================

def get_base_report_queryset():
    return visit.objects.select_related(
        "visitor",
        "employee",
        "employee__emp_cmp",
        "employee__emp_bra_code",
        "employee__emp_dep_code",
        "visitor_card",
    ).all()


def get_filtered_history_queryset(request):
    access = get_report_access_settings(request)
    selected_company, selected_branch = get_selected_company_branch(request, access)
    date_settings = get_report_date_range(request)

    visits = get_base_report_queryset()
    visits = apply_report_access_filter(visits, access, selected_company, selected_branch)
    visits = apply_date_filter(visits, date_settings)

    # Filter Parameters
    selected_visitor = normalize_filter_value(request.GET.get("visitor"))
    selected_employee = normalize_filter_value(request.GET.get("employee"))
    selected_purpose = normalize_filter_value(request.GET.get("purpose"))
    selected_status = normalize_filter_value(request.GET.get("status"))

    if selected_visitor:
        try:
            v_id = int(selected_visitor)
            visits = visits.filter(
                Q(visitor_id=v_id) | Q(visitor__visitor_id=v_id) | Q(visitor__pk=v_id)
            )
        except ValueError:
            visits = visits.filter(
                Q(visitor__visitor_name__iexact=selected_visitor) | Q(visitor_id=selected_visitor)
            )

    if selected_employee:
        try:
            emp_id = int(selected_employee)
            visits = visits.filter(Q(employee_id=emp_id) | Q(employee__pk=emp_id))
        except ValueError:
            visits = visits.filter(employee__emp_name__iexact=selected_employee)

    if selected_purpose:
        purpose_obj = sys_pur_master.objects.filter(pur_id=selected_purpose).first()
        if purpose_obj:
            visits = visits.filter(visit_purpose__iexact=purpose_obj.pur_purpose)
        else:
            visits = visits.filter(visit_purpose__iexact=selected_purpose)

    if selected_status:
        visits = visits.filter(status__iexact=selected_status)

    visits = visits.order_by("-check_in_time")

    annotated_visits = []
    for v in visits:
        duration_str = "-"
        if v.check_in_time and v.check_out_time:
            dur = v.check_out_time - v.check_in_time
            duration_str = format_duration(dur)
        annotated_visits.append({
            "object": v,
            "duration_display": duration_str,
        })

    # GROUP BY DEPARTMENT FOR THE HISTORY GRAPH
    department_qs = (
        visits.filter(employee__isnull=False)
        .values("employee__emp_dep_code__dep_desc")
        .annotate(total=Count("visit_id"))
        .order_by("-total")[:8]
    )
    department_labels = [d["employee__emp_dep_code__dep_desc"] or "Unassigned" for d in department_qs]
    department_counts = [d["total"] for d in department_qs]

    title_suffix = date_settings["title_suffix"]
    report_title = "Visit History Report"
    if title_suffix:
        report_title = f"{report_title} - {title_suffix}"

    return {
        "visits_data": annotated_visits,
        "visits": visits,
        "report_title": report_title,
        "access": access,
        "selected_company": selected_company or "ALL",
        "selected_branch": selected_branch or "ALL",
        "selected_visitor": selected_visitor or "ALL",
        "selected_employee": selected_employee or "ALL",
        "selected_purpose": selected_purpose or "ALL",
        "selected_status": selected_status or "ALL",
        "date_settings": date_settings,
        "history_department_labels": department_labels,
        "history_department_counts": department_counts,
    }


def get_filtered_summary_queryset(request):
    access = get_report_access_settings(request)
    selected_company, selected_branch = get_selected_company_branch(request, access)
    date_settings = get_report_date_range(request)

    visits = get_base_report_queryset()
    visits = apply_report_access_filter(visits, access, selected_company, selected_branch)
    visits = apply_date_filter(visits, date_settings)

    group_by_param = (request.GET.get("group_by") or "purpose").strip().lower()

    mapping = {
        "purpose": ("visit_purpose", "Purpose"),
        "company": ("employee__emp_cmp__cmp_desc", "Company"),
        "branch": ("employee__emp_bra_code__bra_desc", "Branch"),
        "department": ("employee__emp_dep_code__dep_desc", "Department"),
        "division": ("employee__emp_dep_code__dep_div_code__div_desc", "Division"),
        "employee": ("employee__emp_name", "Employee"),
        "visitor": ("visitor__visitor_name", "Visitor"),
    }

    group_field, group_label = mapping.get(group_by_param, mapping["purpose"])

    visit_duration = ExpressionWrapper(
        F("check_out_time") - F("check_in_time"),
        output_field=DurationField(),
    )

    summary_queryset = (
        visits.values(group_field)
        .annotate(
            visitor_count=Count("visitor_id", distinct=True),
            total_visits=Count("visit_id"),
            total_visit_time=Sum(visit_duration, filter=Q(check_out_time__isnull=False)),
        )
        .order_by("-total_visits", group_field)
    )

    summary_rows = []
    chart_category_labels = []
    chart_visits_counts = []

    for item in summary_queryset[:8]:
        category_name = item[group_field] or "Not Specified / Others"

        summary_rows.append({
            "dimension_value": category_name,
            "visitor_count": item["visitor_count"],
            "total_visits": item["total_visits"],
            "total_visit_time_display": format_duration(item["total_visit_time"]),
        })

        chart_category_labels.append(category_name)
        chart_visits_counts.append(item["total_visits"])

    total_unique_visitors = visits.values("visitor_id").distinct().count()
    total_visits = visits.count()
    total_duration_val = visits.filter(check_out_time__isnull=False).aggregate(total=Sum(visit_duration))["total"]

    title_suffix = date_settings["title_suffix"]
    report_title = f"Visit Summary Report (Grouped by {group_label})"
    if title_suffix:
        report_title = f"{report_title} - {title_suffix}"

    return {
        "summary_rows": summary_rows,
        "report_title": report_title,
        "group_label": group_label,
        "selected_group_by": group_by_param,
        "access": access,
        "selected_company": selected_company or "ALL",
        "selected_branch": selected_branch or "ALL",
        "date_settings": date_settings,
        "total_unique_visitors": total_unique_visitors,
        "total_visits": total_visits,
        "total_duration_display": format_duration(total_duration_val),
        "summary_chart_labels": chart_category_labels,
        "summary_chart_visits": chart_visits_counts,
    }


# =========================================================
# REPORT VIEWS & PDF EXPORTS
# =========================================================

@login_required
@permission_required("reports.view_reports", raise_exception=True)
def report_summary(request):
    access = get_report_access_settings(request)
    selected_company, selected_branch = get_selected_company_branch(request, access)
    filter_options = get_report_filter_options(access, selected_company, selected_branch)
    date_settings = get_report_date_range(request)

    summary_data = get_filtered_summary_queryset(request)

    context = {
        "report_generated": True,
        "has_report_access": access["has_access"],
        "can_select_company": access["can_select_company"],
        "can_select_branch": access["can_select_branch"],
        "companies": filter_options["companies"],
        "branches": filter_options["branches"],
        "selected_company": selected_company or "ALL",
        "selected_branch": selected_branch or "ALL",
        "published_date": timezone.localtime().strftime("%d %B %Y"),
        "published_time": timezone.localtime().strftime("%I:%M %p"),
        "generated_by": request.user.username,
        **date_settings,
    }

    if summary_data:
        context.update(summary_data)

    return render(request, "reports/report_summary.html", context)


@login_required
@permission_required("reports.view_reports", raise_exception=True)
def report_history(request):
    access = get_report_access_settings(request)
    selected_company, selected_branch = get_selected_company_branch(request, access)
    filter_options = get_report_filter_options(access, selected_company, selected_branch)

    date_settings = get_report_date_range(request)

    report_generated = True
    history_data = get_filtered_history_queryset(request)

    employees = filter_options["employees"]
    formatted_employees = []
    for emp in employees:
        des_desc = ""
        for attr in ["emp_des_code", "emp_designation", "emp_desig", "designation"]:
            if hasattr(emp, attr):
                val = getattr(emp, attr)
                if val:
                    des_desc = getattr(val, "des_desc", getattr(val, "des_name", str(val)))
                    break
        formatted_name = f"{emp.emp_name} ({des_desc})" if des_desc else emp.emp_name
        formatted_employees.append({"id": emp.id, "name": formatted_name})

    context = {
        "report_generated": report_generated,
        "has_report_access": access["has_access"],
        "can_select_company": access["can_select_company"],
        "can_select_branch": access["can_select_branch"],
        "companies": filter_options["companies"],
        "branches": filter_options["branches"],
        "formatted_employees": formatted_employees,
        "visitors": visitor.objects.all().order_by("visitor_name"),
        "purposes": sys_pur_master.objects.filter(pur_active=True).order_by("pur_purpose"),
        "selected_company": selected_company or "ALL",
        "selected_branch": selected_branch or "ALL",
        "selected_visitor": request.GET.get("visitor") or "ALL",
        "selected_employee": request.GET.get("employee") or "ALL",
        "selected_purpose": request.GET.get("purpose") or "ALL",
        "selected_status": request.GET.get("status") or "ALL",
        "published_date": timezone.localtime().strftime("%d %B %Y"),
        "published_time": timezone.localtime().strftime("%I:%M %p"),
        "generated_by": request.user.username,
        **date_settings,
    }

    if history_data:
        context.update(history_data)

    return render(request, "reports/report_history.html", context)


def render_pdf_response(template_name, context, filename):
    template = get_template(template_name)
    html = template.render(context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF.", status=500)
    return response


@login_required
@permission_required("reports.download_reports", raise_exception=True)
def download_summary_pdf(request):
    summary_data = get_filtered_summary_queryset(request)
    context = {
        **summary_data,
        "published_date": timezone.localtime().strftime("%d %B %Y"),
        "published_time": timezone.localtime().strftime("%I:%M %p"),
        "generated_by": request.user.username,
    }
    return render_pdf_response("reports/pdf_summary_report.html", context, "visit_summary_report.pdf")


@login_required
@permission_required("reports.download_reports", raise_exception=True)
def download_history_pdf(request):
    history_data = get_filtered_history_queryset(request)
    context = {
        **history_data,
        "published_date": timezone.localtime().strftime("%d %B %Y"),
        "published_time": timezone.localtime().strftime("%I:%M %p"),
        "generated_by": request.user.username,
    }
    return render_pdf_response("reports/pdf_history_report.html", context, "visit_history_report.pdf")