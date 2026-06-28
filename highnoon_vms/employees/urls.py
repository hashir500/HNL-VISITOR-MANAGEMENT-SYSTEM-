from django.urls import path
from . import views

urlpatterns = [
    path("departments/", views.department_list, name="department_list"),
    path("departments/add/", views.department_create, name="department_create"),
    path("departments/edit/<int:department_id>/", views.department_update, name="department_update"),
    path("departments/delete/<int:department_id>/", views.department_delete, name="department_delete"),

    path("employees/", views.employee_list, name="employee_list"),
    path("employees/add/", views.employee_create, name="employee_create"),
    path("employees/edit/<int:employee_id>/",views.employee_update,name="employee_update",),
    path("employees/delete/<int:employee_id>/",views.employee_delete,name="employee_delete",),
]