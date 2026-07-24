from django.urls import path
from . import views


urlpatterns = [
    # visitor card urls
    path("cards/", views.visitor_card_list, name="visitor_card_list"),
    path("cards/create/", views.visitor_card_create, name="visitor_card_create"),
    path("cards/update/<int:pk>/", views.visitor_card_update, name="visitor_card_update"),
    path("cards/delete/<int:pk>/", views.visitor_card_delete, name="visitor_card_delete"),
    path("visitor-cards/import/upload/", views.visitor_card_import_upload, name="visitor_card_import_upload"),
    path("visitor-cards/import/process/", views.visitor_card_import_process, name="visitor_card_import_process"),
    path("visitor-cards/delete-all/", views.visitor_card_delete_all, name="visitor_card_delete_all"),

    # company type urls
    path("company-types/", views.company_type_list, name="company_type_list"),
    path("company-types/create/", views.company_type_create, name="company_type_create"),
    path("company-types/update/<int:pk>/", views.company_type_update, name="company_type_update"),
    path("company-types/delete/<int:pk>/", views.company_type_delete, name="company_type_delete"),

    # visitor urls
    path("visitors/", views.visitor_list, name="visitor_list"),
    path("visitors/create/", views.visitor_create, name="visitor_create"),
    path("visitors/update/<int:visitor_id>/", views.visitor_update, name="visitor_update"),
    path("visitors/delete/<int:visitor_id>/", views.visitor_delete, name="visitor_delete"),
]