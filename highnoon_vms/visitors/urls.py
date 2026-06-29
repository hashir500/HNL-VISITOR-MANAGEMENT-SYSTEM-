from django.urls import path
from . import views

urlpatterns = [
    path("visitor-cards/", views.visitor_card_list, name="visitor_card_list"),
]