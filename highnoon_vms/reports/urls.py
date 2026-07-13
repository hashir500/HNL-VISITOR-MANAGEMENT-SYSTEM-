from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.report_page_redirect,
        name="report_page",
    ),

    path(
        "summary/",
        views.report_summary,
        name="report_summary",
    ),
    path(
        "summary/download/",
        views.download_summary_pdf,
        name="download_summary_pdf",
    ),

    path(
        "history/",
        views.report_history,
        name="report_history",
    ),
    path(
        "history/download/",
        views.download_history_pdf,
        name="download_history_pdf",
    ),

    path(
        "download/",
        views.download_report_pdf_redirect,
        name="download_report_pdf",
    ),
]