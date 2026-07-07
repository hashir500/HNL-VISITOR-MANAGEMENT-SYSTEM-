from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect


def redirect_after_login(user):
    if user.has_perm("dashboard.view_dashboard"):
        return redirect("dashboard_page")

    if user.has_perm("visits.view_visit"):
        return redirect("visit_list")

    if user.has_perm("visitors.view_visitor"):
        return redirect("visitor_list")

    if user.has_perm("reports.view_reports"):
        return redirect("report_page")

    return redirect("logout")


def login_page(request):
    if request.user.is_authenticated:
        return redirect_after_login(request.user)

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect_after_login(user)

        messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")


def logout_user(request):
    logout(request)
    return redirect("login")