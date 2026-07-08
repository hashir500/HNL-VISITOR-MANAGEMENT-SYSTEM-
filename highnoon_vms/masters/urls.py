from django.urls import path
from . import views

urlpatterns = [
    path("companies/", views.company_list, name="company_list"),
    path("companies/create/", views.company_create, name="company_create"),
    path("companies/update/<int:pk>/", views.company_update, name="company_update"),
    path("companies/delete/<int:pk>/", views.company_delete, name="company_delete"),
    path("branches/", views.branch_list, name="branch_list"),
    path("branches/create/", views.branch_create, name="branch_create"),
    path("branches/update/<int:pk>/", views.branch_update, name="branch_update"),
    path("branches/delete/<int:pk>/", views.branch_delete, name="branch_delete"),
]