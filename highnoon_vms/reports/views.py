from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa
from datetime import datetime, timedelta
from visits.models import visit


def report_page(request):
    return render(request, "reports/report_page.html")


def download_report_pdf(request):
    report_type = request.GET.get("report_type")

    visits = visit.objects.all().order_by("-check_in_time")
    report_title = "Visit Report"

    if report_type == "daily":
        selected_date = request.GET.get("date")
        date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
        visits = visits.filter(check_in_time__date=date_obj)
        report_title = f"Daily Visit Report - {date_obj.strftime('%d %B %Y')}"

    elif report_type == "weekly":
        week_start = request.GET.get("week_start")
        start_date = datetime.strptime(week_start, "%Y-%m-%d").date()
        end_date = start_date + timedelta(days=6)
        visits = visits.filter(check_in_time__date__range=[start_date, end_date])
        report_title = f"Weekly Visit Report - {start_date.strftime('%d %B %Y')} to {end_date.strftime('%d %B %Y')}"

    elif report_type == "monthly":
        selected_month = request.GET.get("month")
        year, month = selected_month.split("-")
        visits = visits.filter(
            check_in_time__year=year,
            check_in_time__month=month
        )
        report_title = f"Monthly Visit Report - {datetime(int(year), int(month), 1).strftime('%B %Y')}"

    template = get_template("reports/pdf_report.html")

    html = template.render({
        "visits": visits,
        "report_title": report_title,
        "published_date": timezone.localtime().strftime("%d %B %Y"),
        "published_time": timezone.localtime().strftime("%I:%M %p"),
        "generated_by": "Admin",
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="visit_report.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)

    return response