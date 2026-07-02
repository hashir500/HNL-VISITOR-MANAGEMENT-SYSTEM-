from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required

from .models import SystemSettings


@login_required
@permission_required("system_setting.view_systemsettings", raise_exception=True)
def system_settings_page(request):

    settings = SystemSettings.objects.first()

    return render(
        request,
        "system_setting/system_settings.html",
        {
            "system_settings": settings,
        },
    )