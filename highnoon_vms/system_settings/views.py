import os
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login
from django.contrib.auth.models import User

from .models import SystemSettings


@login_required
@permission_required("system_setting.view_systemsettings", raise_exception=True)
def system_settings_page(request):
    settings = SystemSettings.objects.first()

    # Fallback Logic: Pull from DB first, if empty check the environment variables
    ms_client_id = (settings.ms_client_id if settings else None) or os.getenv('MS_CLIENT_ID', '')
    ms_tenant_id = (settings.ms_tenant_id if settings else None) or os.getenv('MS_TENANT_ID', '')
    ms_client_secret = (settings.ms_client_secret if settings else None) or os.getenv('MS_CLIENT_SECRET', '')
    ms_redirect_uri = (settings.ms_redirect_uri if settings else None) or os.getenv('MS_REDIRECT_URI', '')

    return render(
        request,
        "system_setting/system_settings.html",
        {
            "system_settings": settings,
            "ms_client_id": ms_client_id,
            "ms_tenant_id": ms_tenant_id,
            "ms_redirect_uri": ms_redirect_uri,
        },
    )


# --- SSO Authentication View Template ---
def microsoft_sso_callback(request):
    # 1. [Insert your OAuth token exchange here to get the email payload from Microsoft]
    user_email = "incoming_user@company.com"  # Placeholder email from Microsoft token

    # 2. Whitelist enforcement: Check if user already exists in the app database
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        return HttpResponseForbidden(
            "Access Denied: Your account is not authorized to access this system. Please contact the administrator."
        )

    # 3. Success: Log the authorized user into the Django session
    login(request, user)
    return redirect('dashboard')