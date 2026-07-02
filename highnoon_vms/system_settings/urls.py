from django.urls import path
from . import views

urlpatterns = [
    path(
        "system-settings/",
        views.system_settings_page,
        name="system_settings_page",
    ),
]


