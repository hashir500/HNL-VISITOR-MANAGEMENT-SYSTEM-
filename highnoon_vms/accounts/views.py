<<<<<<< HEAD
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect


def redirect_after_login(user):
=======
import requests

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from .microsoft import build_msal_app, get_auth_url, SCOPES


def redirect_after_login(user):
    if not user.groups.exists() and not user.is_superuser:
        return redirect("access_pending")

>>>>>>> 4e3f11a (user creation and enhanced ui)
    if user.has_perm("dashboard.view_dashboard"):
        return redirect("dashboard_page")

    if user.has_perm("visits.view_visit"):
        return redirect("visit_list")

    if user.has_perm("visitors.view_visitor"):
        return redirect("visitor_list")

    if user.has_perm("reports.view_reports"):
        return redirect("report_page")

<<<<<<< HEAD
    return redirect("logout")
=======
    return redirect("access_pending")
>>>>>>> 4e3f11a (user creation and enhanced ui)


def login_page(request):
    if request.user.is_authenticated:
        return redirect_after_login(request.user)

    if request.method == "POST":
<<<<<<< HEAD
        username = request.POST.get("username")
        password = request.POST.get("password")

=======
        username = (request.POST.get("username") or "").strip().lower()
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "Invalid username or password.")
            return render(request, "accounts/login.html")

        if hasattr(user_obj, "profile") and user_obj.profile.account_type == "m365":
            messages.error(
                request,
                "This account uses Microsoft 365. Please click 'Sign in with Microsoft 365'."
            )
            return render(request, "accounts/login.html")

>>>>>>> 4e3f11a (user creation and enhanced ui)
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
<<<<<<< HEAD
    return redirect("login")
=======
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

    try:
        user = User.objects.get(username=email)
    except User.DoesNotExist:
        return redirect("access_pending")

    if not hasattr(user, "profile"):
        return redirect("access_pending")

    if user.profile.account_type != "m365":
        return redirect("access_pending")

    if not user.groups.exists() and not user.is_superuser:
        return redirect("access_pending")

    login(
        request,
        user,
        backend="django.contrib.auth.backends.ModelBackend",
    )

    return redirect_after_login(user)


def access_pending(request):
    return render(request, "accounts/access_pending.html")
>>>>>>> 4e3f11a (user creation and enhanced ui)
