from django.urls import path
from . import views

urlpatterns = [
    path("departments/", views.department_list, name="department_list"),
    path("departments/add/", views.department_create, name="department_create"),
    path("departments/edit/<int:department_id>/", views.department_update, name="department_update"),
    path("departments/delete/<int:department_id>/", views.department_delete, name="department_delete"),
]