import requests

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect

from masters.models import sys_usr_system
from .microsoft import build_msal_app, get_auth_url, SCOPES


def redirect_after_login(user):
    if not user.groups.exists() and not user.is_superuser:
        return redirect("access_pending")

    if user.has_perm("dashboard.view_dashboard"):
        return redirect("dashboard_page")

    if user.has_perm("visits.view_visit"):
        return redirect("visit_list")

    if user.has_perm("visitors.view_visitor"):
        return redirect("visitor_list")

    if user.has_perm("reports.view_reports"):
        return redirect("report_page")

    return redirect("access_pending")


def login_page(request):
    if request.user.is_authenticated:
        return redirect_after_login(request.user)

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip().lower()
        password = request.POST.get("password")

        sys_user = sys_usr_system.objects.filter(
            usr_loginID__iexact=username
        ).first()

        if not sys_user:
            messages.error(request, "Invalid username or password.")
            return render(request, "accounts/login.html")

        if (sys_user.usr_auth or "").upper() == "SSO":
            messages.error(
                request,
                "This account uses Microsoft 365. Please click 'Sign in with Microsoft 365'."
            )
            return render(request, "accounts/login.html")

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


def microsoft_login(request):
    return redirect(get_auth_url())


def microsoft_callback(request):
    code = request.GET.get("code")

    if not code:
        messages.error(request, "Microsoft login failed.")
        return redirect("login")

    app = build_msal_app()

    result = app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPES,
        redirect_uri=request.build_absolute_uri("/microsoft_sso/callback/"),
    )

    if "access_token" not in result:
        messages.error(request, "Could not get Microsoft access token.")
        return redirect("login")

    user_data = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {result['access_token']}"},
    ).json()

    email = user_data.get("mail") or user_data.get("userPrincipalName")

    if not email:
        messages.error(request, "Microsoft account email not found.")
        return redirect("login")

    email = email.strip().lower()

    sys_user = sys_usr_system.objects.filter(
        usr_loginID__iexact=email,
        usr_auth__iexact="SSO"
    ).first()

    if not sys_user:
        return redirect("access_pending")

    name_parts = (sys_user.usr_name or "").strip().split(" ", 1)
    first_name = name_parts[0] if len(name_parts) > 0 else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    django_user, created = User.objects.get_or_create(
        username=sys_user.usr_loginID,
        defaults={
            "email": sys_user.usr_email,
            "first_name": first_name,
            "last_name": last_name,
            "is_active": True,
        }
    )

    django_user.email = sys_user.usr_email
    django_user.first_name = first_name
    django_user.last_name = last_name
    django_user.is_active = True
    django_user.set_unusable_password()
    django_user.save()

    django_user.groups.clear()

    if sys_user.usr_access_group:
        group = Group.objects.filter(id=sys_user.usr_access_group).first()
        if group:
            django_user.groups.add(group)

    login(
        request,
        django_user,
        backend="django.contrib.auth.backends.ModelBackend",
    )

    return redirect_after_login(django_user)


def access_pending(request):
    return render(request, "accounts/access_pending.html")