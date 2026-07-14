from django.urls import path
from . import views

urlpatterns = [
    # Main Dashboard Filtered Analytics Pages
    path("summary/", views.report_summary, name="report_summary"),
    path("history/", views.report_history, name="report_history"),
    
    # Document Exporters / Download Links
    path("summary/download/", views.download_summary_pdf, name="download_summary_pdf"),
    path("history/download/", views.download_history_pdf, name="download_history_pdf"),
]