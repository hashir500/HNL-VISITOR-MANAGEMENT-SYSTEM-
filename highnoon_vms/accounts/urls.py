from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_page, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("microsoft_sso/login/", views.microsoft_login, name="microsoft_login"),
    path("microsoft_sso/callback/", views.microsoft_callback, name="microsoft_callback"),
    path("access-pending/", views.access_pending, name="access_pending"),
]