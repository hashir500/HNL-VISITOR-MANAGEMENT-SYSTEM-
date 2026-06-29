from django.urls import path
from . import views


urlpatterns = [
# visitor card urls
    path("cards/", views.visitor_card_list, name="visitor_card_list"),
    path("cards/create/", views.visitor_card_create, name="visitor_card_create"),
    path("cards/update/<int:pk>/", views.visitor_card_update, name="visitor_card_update"),
    path("cards/delete/<int:pk>/", views.visitor_card_delete, name="visitor_card_delete"),

# visitor urls
    path("visitors/", views.visitor_list, name="visitor_list"),
    path("visitors/create/", views.visitor_create, name="visitor_create"),
    path("visitors/update/<int:visitor_id>/", views.visitor_update, name="visitor_update"),
    path("visitors/delete/<int:visitor_id>/", views.visitor_delete, name="visitor_delete"),
]