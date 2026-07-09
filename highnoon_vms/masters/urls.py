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

    path("divisions/", views.division_list, name="division_list"),
    path("divisions/create/", views.division_create, name="division_create"),
    path("divisions/update/<int:pk>/", views.division_update, name="division_update"),
    path("divisions/delete/<int:pk>/", views.division_delete, name="division_delete"),

    path("departments/", views.department_master_list, name="department_master_list"),
    path("departments/create/", views.department_master_create, name="department_master_create"),
    path("departments/update/<int:pk>/", views.department_master_update, name="department_master_update"),
    path("departments/delete/<int:pk>/", views.department_master_delete, name="department_master_delete"),
    path("departments/import/upload/", views.department_import_upload, name="department_import_upload"),
    path("departments/import/process/", views.department_import_process, name="department_import_process"),

    path("employees/", views.employee_master_list, name="employee_master_list"),
    path("employees/create/", views.employee_master_create, name="employee_master_create"),
    path("employees/update/<int:pk>/", views.employee_master_update, name="employee_master_update"),
    path("employees/delete/<int:pk>/", views.employee_master_delete, name="employee_master_delete"),
    path("employees/import/upload/", views.employee_import_upload, name="employee_import_upload"),
    path("employees/import/process/", views.employee_import_process, name="employee_import_process"),

    path("purposes/", views.purpose_list, name="purpose_list"),
    path("purposes/create/", views.purpose_create, name="purpose_create"),
    path("purposes/update/<int:pk>/", views.purpose_update, name="purpose_update"),
    path("purposes/delete/<int:pk>/", views.purpose_delete, name="purpose_delete"),

   
    path("users/", views.user_master_ui, name="user_master_ui"),
    path(
    "users/fetch-employee/<str:emp_pno>/",
    views.fetch_employee_details,
    name="fetch_employee_details"
),
]