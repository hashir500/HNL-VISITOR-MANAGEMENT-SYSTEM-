from django.urls import path
from . import views

urlpatterns = [
    path("reports/", views.report_page, name="report_page"),
    path("reports/download/", views.download_report_pdf, name="download_report_pdf"),
]