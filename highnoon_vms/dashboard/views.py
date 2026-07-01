from django.shortcuts import render

def dashboard_page(request):
    return render(request, "dashboards/dashboard_page.html")