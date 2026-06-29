from django.shortcuts import render
from .models import visitor_card


def visitor_card_list(request):
    cards = visitor_card.objects.all()
    return render(request, "visitors/visitor_card_list.html", {"cards": cards})

