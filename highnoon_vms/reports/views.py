from datetime import datetime, timedelta

from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.utils import timezone
from django.contrib.auth.decorators import login_required, permission_required

from xhtml2pdf import pisa

from visits.models import visit


<<<<<<< HEAD
@login_required
@permission_required("reports.view_reports", raise_exception=True)
def report_page(request):
    return render(request, "reports/report_page.html")


@login_required
@permission_required("reports.download_reports", raise_exception=True)
def download_report_pdf(request):
=======
def get_filtered_report(request):
>>>>>>> 4e3f11a (user creation and enhanced ui)
    report_type = request.GET.get("report_type")

    visits = visit.objects.all().order_by("-check_in_time")
    report_title = "Visit Report"

    if report_type == "daily":
        selected_date = request.GET.get("date")
        date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()

        start_date_time = timezone.make_aware(
            datetime.combine(date_obj, datetime.min.time())
        )
        end_date_time = timezone.make_aware(
            datetime.combine(date_obj, datetime.max.time())
        )

        visits = visits.filter(check_in_time__range=(start_date_time, end_date_time))
        report_title = f"Daily Visit Report - {date_obj.strftime('%d %B %Y')}"

    elif report_type == "weekly":
        week_start = request.GET.get("week_start")
        start_date = datetime.strptime(week_start, "%Y-%m-%d").date()
        end_date = start_date + timedelta(days=6)

        start_date_time = timezone.make_aware(
            datetime.combine(start_date, datetime.min.time())
        )
        end_date_time = timezone.make_aware(
            datetime.combine(end_date, datetime.max.time())
        )

        visits = visits.filter(check_in_time__range=(start_date_time, end_date_time))
        report_title = f"Weekly Visit Report - {start_date.strftime('%d %B %Y')} to {end_date.strftime('%d %B %Y')}"

    elif report_type == "monthly":
        selected_month = request.GET.get("month")
        year, month = selected_month.split("-")

<<<<<<< HEAD
=======
        year = int(year)
        month = int(month)

        start_date = datetime(year, month, 1).date()

        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()

        start_date_time = timezone.make_aware(
            datetime.combine(start_date, datetime.min.time())
        )
        end_date_time = timezone.make_aware(
            datetime.combine(end_date, datetime.min.time())
        )

        visits = visits.filter(
            check_in_time__gte=start_date_time,
            check_in_time__lt=end_date_time
        )

        report_title = f"Monthly Visit Report - {datetime(year, month, 1).strftime('%B %Y')}"

    return visits, report_title


@login_required
@permission_required("reports.view_reports", raise_exception=True)
def report_page(request):
    visits = None
    report_title = None
    report_generated = False

    if request.GET.get("report_type"):
        visits, report_title = get_filtered_report(request)
        report_generated = True

    return render(request, "reports/report_page.html", {
        "visits": visits,
        "report_title": report_title,
        "report_generated": report_generated,
        "published_date": timezone.localtime().strftime("%d %B %Y"),
        "published_time": timezone.localtime().strftime("%I:%M %p"),
        "generated_by": request.user.username,
        "selected_report_type": request.GET.get("report_type", ""),
        "selected_date": request.GET.get("date", ""),
        "selected_week_start": request.GET.get("week_start", ""),
        "selected_month": request.GET.get("month", ""),
    })


@login_required
@permission_required("reports.download_reports", raise_exception=True)
def download_report_pdf(request):
    visits, report_title = get_filtered_report(request)

>>>>>>> 4e3f11a (user creation and enhanced ui)
    template = get_template("reports/pdf_reports.html")

    html = template.render({
        "visits": visits,
        "report_title": report_title,
        "published_date": timezone.localtime().strftime("%d %B %Y"),
        "published_time": timezone.localtime().strftime("%I:%M %p"),
        "generated_by": request.user.username,
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="visit_report.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)

    return response