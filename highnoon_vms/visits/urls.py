from django.urls import path
from . import views

urlpatterns = [
    path("visits/", views.visit_list, name="visit_list"),
    path("visits/create/", views.visit_create, name="visit_create"),
    path("visits/checkout/<int:visit_id>/", views.visit_checkout, name="visit_checkout"),
    path("backlogs/", views.backlog_list_create, name="backlog_list_create"),
]