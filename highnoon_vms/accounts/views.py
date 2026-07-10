import requests

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

from masters.models import sys_usr_system
from .microsoft import build_msal_app, get_auth_url, SCOPES

def get_redirect_url_after_login(user):
    if not user.groups.exists() and not user.is_superuser:
        return reverse("access_pending")

    if user.has_perm("dashboard.view_dashboard"):
        return reverse("dashboard_page")

    if user.has_perm("visits.view_visit"):
        return reverse("visit_list")

    if user.has_perm("visitors.view_visitor"):
        return reverse("visitor_list")

    if user.has_perm("reports.view_reports"):
        return reverse("report_page")

    return reverse("access_pending")

def redirect_after_login(user):
    return redirect(get_redirect_url_after_login(user))


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

            request.session["show_login_transition"] = True
            request.session["login_transition_target"] = (
                get_redirect_url_after_login(user)
                )

            return redirect("login_transition")

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
        redirect_uri=request.build_absolute_uri(
            "/microsoft_sso/callback/"
        ),
    )

    if "access_token" not in result:
        messages.error(
            request,
            "Could not get Microsoft access token."
        )
        return redirect("login")

    try:
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={
                "Authorization": (
                    f"Bearer {result['access_token']}"
                )
            },
            timeout=15,
        )
        response.raise_for_status()
        user_data = response.json()

    except requests.RequestException:
        messages.error(
            request,
            "Could not retrieve Microsoft account details."
        )
        return redirect("login")

    email = (
        user_data.get("mail")
        or user_data.get("userPrincipalName")
    )

    if not email:
        messages.error(
            request,
            "Microsoft account email was not found."
        )
        return redirect("login")

    email = email.strip().lower()

    try:
        user = User.objects.get(
            username__iexact=email
        )

    except User.DoesNotExist:
        messages.error(
            request,
            "This Microsoft account is not registered."
        )
        return redirect("access_pending")

    if not user.groups.exists() and not user.is_superuser:
        messages.error(
            request,
            "This account does not have an assigned access group."
        )
        return redirect("access_pending")

    login(
        request,
        user,
        backend="django.contrib.auth.backends.ModelBackend",
    )

    request.session["show_login_transition"] = True
    request.session["login_transition_target"] = (
        get_redirect_url_after_login(user)
    )

    return redirect("login_transition")

@login_required
def login_transition(request):
    if not request.session.pop("show_login_transition", False):
        return redirect_after_login(request.user)

    target_url = request.session.pop(
        "login_transition_target",
        None,
    )

    if not target_url:
        target_url = get_redirect_url_after_login(request.user)

    display_name = (
        request.user.first_name.strip()
        if request.user.first_name
        else request.user.username.split("@")[0]
    )

    return render(
        request,
        "accounts/login_transition.html",
        {
            "target_url": target_url,
            "display_name": display_name,
        },
    )

def access_pending(request):
    return render(request, "accounts/access_pending.html")