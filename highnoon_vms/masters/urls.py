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
]