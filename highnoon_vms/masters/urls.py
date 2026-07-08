from django.urls import path
from . import views

urlpatterns = [
    path("companies/", views.company_list, name="company_list"),
    path("companies/create/", views.company_create, name="company_create"),
    path("companies/update/<int:pk>/", views.company_update, name="company_update"),
    path("companies/delete/<int:pk>/", views.company_delete, name="company_delete"),
]