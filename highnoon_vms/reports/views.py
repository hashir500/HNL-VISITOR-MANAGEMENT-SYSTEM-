from calendar import monthrange
from datetime import date, datetime, time, timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.db.models import (
    Avg,
    Count,
    DurationField,
    ExpressionWrapper,
    F,
    Q,
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


from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


# =========================================================
# GENERAL HELPERS
# =========================================================


def normalize_filter_value(value):
    """
    Convert empty and ALL values into None.
    """

    value = (value or "").strip()

    if not value or value.upper() == "ALL":
        return None

    return value


def safe_parse_date(value, default_value=None):
    """
    Parse YYYY-MM-DD safely.
    """

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()
    except (TypeError, ValueError):
        return default_value


def safe_parse_month(value, default_value=None):
    """
    Parse YYYY-MM safely.

    Returns:
        (year, month)
    """

    try:
        year_text, month_text = value.split("-")

        year = int(year_text)
        month = int(month_text)

        if month < 1 or month > 12:
            raise ValueError

        return year, month

    except (AttributeError, TypeError, ValueError):
        if default_value:
            return default_value.year, default_value.month

        return None, None


def safe_parse_year(value, default_value=None):
    """
    Parse a year safely.
    """

    try:
        return int(value)
    except (TypeError, ValueError):
        return default_value


def make_start_datetime(selected_date):
    return timezone.make_aware(
        datetime.combine(
            selected_date,
            time.min,
        )
    )


def make_end_datetime(selected_date):
    return timezone.make_aware(
        datetime.combine(
            selected_date,
            time.max,
        )
    )


def format_duration(duration_value):
    """
    Convert a timedelta into a readable duration.
    """

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

        return (
            f"{hours} {hour_label} "
            f"{minutes} {minute_label}"
        )

    if hours:
        hour_label = "hr" if hours == 1 else "hrs"
        return f"{hours} {hour_label}"

    minute_label = "min" if total_minutes == 1 else "mins"
    return f"{total_minutes} {minute_label}"


# =========================================================
# COMPANY / BRANCH ACCESS
# =========================================================


def get_logged_in_vms_user(request):
    """
    Match the logged-in Django user with sys_usr_system.
    """

    if request.user.is_superuser:
        return None

    login_id = (
        request.user.username
        or request.user.email
        or ""
    ).strip().lower()

    return (
        sys_usr_system.objects
        .select_related(
            "usr_company",
            "usr_bra_code",
        )
        .filter(
            usr_loginID__iexact=login_id
        )
        .first()
    )


def get_report_access_settings(request):
    """
    Resolve Company and Branch access.
    """

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

    company_code = (
        user_master.usr_company.cmp_code
        if user_master.usr_company
        else None
    )

    branch_code = (
        user_master.usr_bra_code.bra_code
        if user_master.usr_bra_code
        else None
    )

    return {
        "has_access": True,
        "user_master": user_master,
        "can_select_company": (
            user_master.usr_company is None
        ),
        "can_select_branch": (
            user_master.usr_bra_code is None
        ),
        "assigned_company_code": company_code,
        "assigned_branch_code": branch_code,
    }


def get_selected_company_branch(request, access):
    if access["can_select_company"]:
        selected_company = normalize_filter_value(
            request.GET.get("company")
        )
    else:
        selected_company = access[
            "assigned_company_code"
        ]

    if access["can_select_branch"]:
        selected_branch = normalize_filter_value(
            request.GET.get("branch")
        )
    else:
        selected_branch = access[
            "assigned_branch_code"
        ]

    return selected_company, selected_branch


def apply_report_access_filter(
    queryset,
    access,
    selected_company=None,
    selected_branch=None,
):
    if not access["has_access"]:
        return queryset.none()

    if not access["can_select_company"]:
        selected_company = access[
            "assigned_company_code"
        ]

    if not access["can_select_branch"]:
        selected_branch = access[
            "assigned_branch_code"
        ]

    if selected_company:
        queryset = queryset.filter(
            employee__emp_cmp__cmp_code=selected_company
        )

    if selected_branch:
        queryset = queryset.filter(
            employee__emp_bra_code__bra_code=selected_branch
        )

    return queryset


def get_report_filter_options(
    access,
    selected_company=None,
    selected_branch=None,
):
    companies = (
        sys_cmp_master.objects
        .all()
        .order_by("cmp_code")
    )

    branches = (
        sys_bra_master.objects
        .all()
        .order_by("bra_code")
    )

    employees = (
        sys_emp_master.objects
        .select_related(
            "emp_cmp",
            "emp_bra_code",
            "emp_dep_code",
        )
        .filter(emp_active=True)
        .order_by("emp_name")
    )

    if not access["has_access"]:
        return {
            "companies": companies.none(),
            "branches": branches.none(),
            "employees": employees.none(),
        }

    if not access["can_select_company"]:
        companies = companies.filter(
            cmp_code=access["assigned_company_code"]
        )

        employees = employees.filter(
            emp_cmp__cmp_code=access[
                "assigned_company_code"
            ]
        )

    elif selected_company:
        employees = employees.filter(
            emp_cmp__cmp_code=selected_company
        )

    if not access["can_select_branch"]:
        branches = branches.filter(
            bra_code=access["assigned_branch_code"]
        )

        employees = employees.filter(
            emp_bra_code__bra_code=access[
                "assigned_branch_code"
            ]
        )

    elif selected_branch:
        employees = employees.filter(
            emp_bra_code__bra_code=selected_branch
        )

    return {
        "companies": companies,
        "branches": branches,
        "employees": employees,
    }


# =========================================================
# DATE FILTERS
# =========================================================


def get_report_date_range(request):
    """
    Resolve explicit Start Date and End Date periods, defaulting to today.
    """
    today = timezone.localdate()

    selected_start_date = request.GET.get("start_date") or today.strftime("%Y-%m-%d")
    selected_end_date = request.GET.get("end_date") or today.strftime("%Y-%m-%d")

    start_date = safe_parse_date(selected_start_date, today)
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
    }


def apply_date_filter(queryset, date_settings):
    start_datetime = date_settings["start_datetime"]
    end_datetime = date_settings["end_datetime"]

    if start_datetime and end_datetime:
        queryset = queryset.filter(
            check_in_time__range=(
                start_datetime,
                end_datetime,
            )
        )
    return queryset


# =========================================================
# SHARED VISIT QUERY
# =========================================================


def get_base_report_queryset():
    return (
        visit.objects
        .select_related(
            "visitor",
            "employee",
            "employee__emp_cmp",
            "employee__emp_bra_code",
            "employee__emp_dep_code",
            "visitor_card",
        )
        .all()
    )


def get_filtered_history_queryset(request):
    access = get_report_access_settings(
        request
    )

    selected_company, selected_branch = (
        get_selected_company_branch(
            request,
            access,
        )
    )

    date_settings = get_report_date_range(
        request
    )

    visits = get_base_report_queryset()

    visits = apply_report_access_filter(
        queryset=visits,
        access=access,
        selected_company=selected_company,
        selected_branch=selected_branch,
    )

    visits = apply_date_filter(
        visits,
        date_settings,
    )

    selected_visitor = normalize_filter_value(
        request.GET.get("visitor")
    )

    selected_employee = normalize_filter_value(
        request.GET.get("employee")
    )

    selected_purpose = normalize_filter_value(
        request.GET.get("purpose")
    )

    selected_status = normalize_filter_value(
        request.GET.get("status")
    )

    selected_card = normalize_filter_value(
        request.GET.get("card")
    )

    if selected_visitor:
        visits = visits.filter(
            visitor_id=selected_visitor
        )

    if selected_employee:
        visits = visits.filter(
            employee_id=selected_employee
        )

    if selected_purpose:
        purpose_obj = (
            sys_pur_master.objects
            .filter(
                pur_id=selected_purpose
            )
            .first()
        )

        if purpose_obj:
            visits = visits.filter(
                visit_purpose__iexact=(
                    purpose_obj.pur_purpose
                )
            )

    if selected_status:
        visits = visits.filter(
            status=selected_status
        )

    if selected_card:
        visits = visits.filter(
            visitor_card_id=selected_card
        )

    visits = visits.order_by(
        "-check_in_time"
    )

    title_suffix = (
        date_settings["title_suffix"]
    )

    report_title = "Visit History Report"

    if title_suffix:
        report_title = (
            f"{report_title} - {title_suffix}"
        )

    return {
        "visits": visits,
        "report_title": report_title,
        "access": access,
        "selected_company": (
            selected_company or "ALL"
        ),
        "selected_branch": (
            selected_branch or "ALL"
        ),
        "selected_visitor": (
            selected_visitor or "ALL"
        ),
        "selected_employee": (
            selected_employee or "ALL"
        ),
        "selected_purpose": (
            selected_purpose or "ALL"
        ),
        "selected_status": (
            selected_status or "ALL"
        ),
        "selected_card": (
            selected_card or "ALL"
        ),
        "date_settings": date_settings,
    }


def get_filtered_summary_queryset(request):
    """
    Return dynamically grouped summary metrics based on the selected dimensional field.
    """
    access = get_report_access_settings(request)
    selected_company, selected_branch = get_selected_company_branch(request, access)
    date_settings = get_report_date_range(request)

    visits = get_base_report_queryset()
    visits = apply_report_access_filter(
        queryset=visits,
        access=access,
        selected_company=selected_company,
        selected_branch=selected_branch,
    )
    visits = apply_date_filter(visits, date_settings)

    # Resolve dynamic Group By mapping configurations
    group_by_param = (request.GET.get("group_by") or "purpose").strip().lower()
    
    # FIX: Remapped dictionary keys to output user-friendly master table text values
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
        visits
        .values(group_field)
        .annotate(
            visitor_count=Count("visitor_id", distinct=True),
            total_visits=Count("visit_id"),
            average_duration=Avg(
                visit_duration,
                filter=Q(check_out_time__isnull=False),
            ),
        )
        .order_by("-visitor_count", group_field)
    )

    summary_rows = []
    for item in summary_queryset:
        summary_rows.append({
            "dimension_value": item[group_field] or "Not Specified / Others",
            "visitor_count": item["visitor_count"],
            "total_visits": item["total_visits"],
            "average_duration": item["average_duration"],
            "average_duration_display": format_duration(item["average_duration"]),
        })

    total_unique_visitors = visits.values("visitor_id").distinct().count()
    total_visits = visits.count()
    overall_average_duration = visits.filter(check_out_time__isnull=False).aggregate(average=Avg(visit_duration))["average"]

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
        "overall_average_duration_display": format_duration(overall_average_duration),
    }


# =========================================================
# OLD URL REDIRECTS
# =========================================================


@login_required
@permission_required(
    "reports.download_reports",
    raise_exception=True,
)
def download_report_pdf_redirect(request):
    target_url = reverse(
        "download_history_pdf"
    )

    if request.GET:
        target_url = (
            f"{target_url}?"
            f"{request.GET.urlencode()}"
        )

    return redirect(target_url)


# =========================================================
# SUMMARY PAGE
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


# =========================================================
# HISTORY PAGE
# =========================================================


@login_required
@permission_required("reports.view_reports", raise_exception=True)
def report_history(request):
    access = get_report_access_settings(request)
    selected_company, selected_branch = get_selected_company_branch(request, access)
    filter_options = get_report_filter_options(access, selected_company, selected_branch)
    
    date_settings = get_report_date_range(request)
    
    report_generated = True
    history_data = get_filtered_history_queryset(request)

    context = {
        "report_generated": report_generated,
        "has_report_access": access["has_access"],
        "can_select_company": access["can_select_company"],
        "can_select_branch": access["can_select_branch"],
        "companies": filter_options["companies"],
        "branches": filter_options["branches"],
        "employees": filter_options["employees"],
        "visitors": visitor.objects.all().order_by("visitor_name"),
        "purposes": sys_pur_master.objects.filter(pur_active=True).order_by("pur_purpose"),
        "cards": visitor_card.objects.all().order_by("CRD_No"),
        "selected_company": selected_company or "ALL",
        "selected_branch": selected_branch or "ALL",
        "selected_visitor": request.GET.get("visitor") or "ALL",
        "selected_employee": request.GET.get("employee") or "ALL",
        "selected_purpose": request.GET.get("purpose") or "ALL",
        "selected_status": request.GET.get("status") or "ALL",
        "selected_card": request.GET.get("card") or "ALL",
        "published_date": timezone.localtime().strftime("%d %B %Y"),
        "published_time": timezone.localtime().strftime("%I:%M %p"),
        "generated_by": request.user.username,
        **date_settings,
    }

    if history_data:
        context.update(history_data)

    return render(request, "reports/report_history.html", context)

# =========================================================
# PDF HELPERS
# =========================================================


def render_pdf_response(
    template_name,
    context,
    filename,
):
    template = get_template(
        template_name
    )

    html = template.render(
        context
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response[
        "Content-Disposition"
    ] = (
        f'attachment; filename="{filename}"'
    )

    pisa_status = pisa.CreatePDF(
        html,
        dest=response,
    )

    if pisa_status.err:
        return HttpResponse(
            "Error generating PDF.",
            status=500,
        )

    return response


# =========================================================
# SUMMARY PDF
# =========================================================


@login_required
@permission_required(
    "reports.download_reports",
    raise_exception=True,
)
def download_summary_pdf(request):
    """
    Generate vertical, beautifully tracked A4 Portrait Summary PDF Reports based on dynamic Group By fields.
    """
    summary_data = get_filtered_summary_queryset(request)

    context = {
        **summary_data,
        "published_date": (
            timezone.localtime().strftime("%d %B %Y")
        ),
        "published_time": (
            timezone.localtime().strftime("%I:%M %p")
        ),
        "generated_by": (
            request.user.username
        ),
    }

    return render_pdf_response(
        template_name=(
            "reports/pdf_summary_report.html"
        ),
        context=context,
        filename="visit_summary_report.pdf",
    )


# =========================================================
# HISTORY PDF — REPORTLAB A4 PORTRAIT
# =========================================================


def reportlab_safe_text(value, default="-"):
    if value is None:
        return default

    text = str(value).strip()
    return text if text else default


def reportlab_filter_label(value, all_label):
    if not value or str(value).upper() == "ALL":
        return all_label

    return str(value)


def draw_history_pdf_footer(canvas, doc):
    """
    Draw page number and footer on every A4 Portrait page.
    """
    page_width, page_height = A4

    canvas.saveState()

    canvas.setStrokeColor(
        colors.HexColor("#CBD5E1")
    )
    canvas.setLineWidth(0.5)

    canvas.line(
        10 * mm,
        10 * mm,
        page_width - 10 * mm,
        10 * mm,
    )

    canvas.setFillColor(
        colors.HexColor("#64748B")
    )
    canvas.setFont(
        "Helvetica",
        7,
    )

    canvas.drawString(
        10 * mm,
        6 * mm,
        "Generated by the Highnoon Visitor Management System",
    )

    canvas.drawRightString(
        page_width - 10 * mm,
        6 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


@login_required
@permission_required(
    "reports.download_reports",
    raise_exception=True,
)
def download_history_pdf(request):
    """
    Generate vertical, beautifully tracked A4 Portrait Visit History Reports.
    """
    history_data = get_filtered_history_queryset(
        request
    )

    visits = list(history_data["visits"])
    report_title = history_data["report_title"]

    selected_company = history_data["selected_company"]
    selected_branch = history_data["selected_branch"]
    selected_visitor = history_data["selected_visitor"]
    selected_employee = history_data["selected_employee"]
    selected_purpose = history_data["selected_purpose"]
    selected_status = history_data["selected_status"]
    selected_card = history_data["selected_card"]

    buffer = BytesIO()
    pdf_page_size = A4

    doc = BaseDocTemplate(
        buffer,
        pagesize=pdf_page_size,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=15 * mm,
        title=report_title,
        author=request.user.username,
        subject="Visitor history report",
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="history_frame",
    )

    doc.addPageTemplates([
        PageTemplate(
            id="a4_portrait_history",
            pagesize=pdf_page_size,
            frames=[frame],
            onPage=draw_history_pdf_footer,
        )
    ])

    styles = getSampleStyleSheet()

    company_style = ParagraphStyle(
        name="HistoryCompanyName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#111827"),
        spaceAfter=3,
    )

    title_style = ParagraphStyle(
        name="HistoryReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#111827"),
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        name="HistoryNormalText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#1F2937"),
    )

    table_text_style = ParagraphStyle(
        name="HistoryTableText",
        parent=normal_style,
        fontSize=6.5,
        leading=7.5,
    )

    header_style = ParagraphStyle(
        name="HistoryTableHeader",
        parent=normal_style,
        fontName="Helvetica-Bold",
        fontSize=6.5,
        leading=7.5,
        textColor=colors.HexColor("#111827"),
    )

    story = []

    # -----------------------------------------------------
    # Heading
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "Highnoon Laboratories Limited",
            company_style,
        )
    )

    story.append(
        Paragraph(
            report_title,
            title_style,
        )
    )

    current_time = timezone.localtime()

    publication_data = [[
        Paragraph(
            (
                f"<b>Published Date:</b> "
                f"{current_time.strftime('%d %B %Y')}"
            ),
            normal_style,
        ),
        Paragraph(
            (
                f"<b>Published Time:</b> "
                f"{current_time.strftime('%I:%M %p')}"
            ),
            normal_style,
        ),
        Paragraph(
            (
                f"<b>Generated By:</b> "
                f"{reportlab_safe_text(request.user.username)}"
            ),
            normal_style,
        ),
    ]]

    publication_table = Table(
        publication_data,
        colWidths=[doc.width / 3] * 3,
        hAlign="LEFT",
    )

    publication_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#94A3B8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story.append(publication_table)
    story.append(Spacer(1, 5))

    # -----------------------------------------------------
    # Filters
    # -----------------------------------------------------

    filter_data = [
        [
            Paragraph("<b>Company:</b> " + reportlab_filter_label(selected_company, "All Companies"), normal_style),
            Paragraph("<b>Branch:</b> " + reportlab_filter_label(selected_branch, "All Branches"), normal_style),
            Paragraph("<b>Visitor:</b> " + reportlab_filter_label(selected_visitor, "All Visitors"), normal_style),
            Paragraph("<b>Employee:</b> " + reportlab_filter_label(selected_employee, "All Employees"), normal_style),
        ],
        [
            Paragraph("<b>Purpose:</b> " + reportlab_filter_label(selected_purpose, "All Purposes"), normal_style),
            Paragraph("<b>Status:</b> " + reportlab_filter_label(selected_status, "All Statuses"), normal_style),
            Paragraph("<b>Card:</b> " + reportlab_filter_label(selected_card, "All Cards"), normal_style),
            Paragraph(f"<b>Total Records:</b> {len(visits)}", normal_style),
        ],
    ]

    filter_table = Table(
        filter_data,
        colWidths=[doc.width / 4] * 4,
        hAlign="LEFT",
    )

    filter_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#94A3B8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )

    story.append(filter_table)
    story.append(Spacer(1, 6))

    # -----------------------------------------------------
    # History rows
    # -----------------------------------------------------

    table_data = [[
        Paragraph("ID", header_style),
        Paragraph("Visitor", header_style),
        Paragraph("Phone", header_style),
        Paragraph("CNIC", header_style),
        Paragraph("Employee", header_style),
        Paragraph("Dept.", header_style),
        Paragraph("Comp", header_style),
        Paragraph("Br", header_style),
        Paragraph("Card", header_style),
        Paragraph("Purpose", header_style),
        Paragraph("Check In", header_style),
        Paragraph("Check Out", header_style),
        Paragraph("Status", header_style),
    ]]

    for visit_obj in visits:
        visitor_obj = visit_obj.visitor
        employee_obj = visit_obj.employee
        card_obj = visit_obj.visitor_card

        employee_text = reportlab_safe_text(employee_obj.emp_name)
        if employee_obj.emp_pno:
            employee_text += f"<br/><font size='5.5'>PNO: {employee_obj.emp_pno}</font>"

        department_code = employee_obj.emp_dep_code.dep_code if employee_obj.emp_dep_code else "-"
        company_code = employee_obj.emp_cmp.cmp_code if employee_obj.emp_cmp else "-"
        branch_code = employee_obj.emp_bra_code.bra_code if employee_obj.emp_bra_code else "-"
        card_number = card_obj.CRD_No if card_obj else "-"

        check_in_text = "-"
        if visit_obj.check_in_time:
            check_in_text = timezone.localtime(visit_obj.check_in_time).strftime("%d-%b-%y<br/>%I:%M %p")

        check_out_text = "-"
        if visit_obj.check_out_time:
            check_out_text = timezone.localtime(visit_obj.check_out_time).strftime("%d-%b-%y<br/>%I:%M %p")

        table_data.append([
            Paragraph(str(visit_obj.visit_id), table_text_style),
            Paragraph(reportlab_safe_text(visitor_obj.visitor_name), table_text_style),
            Paragraph(reportlab_safe_text(visitor_obj.visitor_phone), table_text_style),
            Paragraph(reportlab_safe_text(visitor_obj.visitor_cnic), table_text_style),
            Paragraph(employee_text, table_text_style),
            Paragraph(department_code, table_text_style),
            Paragraph(company_code, table_text_style),
            Paragraph(branch_code, table_text_style),
            Paragraph(reportlab_safe_text(card_number), table_text_style),
            Paragraph(reportlab_safe_text(visit_obj.visit_purpose), table_text_style),
            Paragraph(check_in_text, table_text_style),
            Paragraph(check_out_text, table_text_style),
            Paragraph(reportlab_safe_text(visit_obj.status), table_text_style),
        ])

    if not visits:
        table_data.append([
            Paragraph("No visit records were found for the selected filters.", normal_style),
            "", "", "", "", "", "", "", "", "", "", "", "",
        ])

    column_widths = [
        7 * mm,     # ID
        18 * mm,    # Visitor
        16 * mm,    # Phone
        17 * mm,    # CNIC
        20 * mm,    # Employee
        9 * mm,     # Department
        9 * mm,     # Company
        9 * mm,     # Branch
        9 * mm,     # Card
        18 * mm,    # Purpose
        23 * mm,    # Check In
        23 * mm,    # Check Out
        12 * mm,    # Status
    ]

    history_table = Table(
        table_data,
        colWidths=column_widths,
        repeatRows=1,
        hAlign="LEFT",
    )

    history_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#64748B")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#94A3B8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (5, 0), (8, -1), "CENTER"),
        ("ALIGN", (12, 0), (12, -1), "CENTER"),
    ]

    if not visits:
        history_style.extend([
            ("SPAN", (0, 1), (-1, 1)),
            ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ])

    history_table.setStyle(TableStyle(history_style))
    story.append(history_table)

    doc.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    filename_timestamp = current_time.strftime("%Y%m%d_%H%M%S")

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="visit_history_{filename_timestamp}.pdf"'
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    response["X-PDF-Generator"] = "ReportLab-A4-Portrait"

    return response