from django.shortcuts import render

def report_page(request):
    return render(request, "reports/report_page.html")