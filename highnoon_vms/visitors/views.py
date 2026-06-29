from django.shortcuts import render, redirect, get_object_or_404
from .models import visitor_card


# visitor card list view
def visitor_card_list(request):
    cards = visitor_card.objects.all()

    return render(
        request,
        "visitors/visitor_card_list.html",
        {"cards": cards},
    )

# visitor card create
def visitor_card_create(request):
    if request.method == "POST":

        visitor_card.objects.create(
            card_color=request.POST["card_color"],
            card_access_level=request.POST["card_access_level"],
        )

    return redirect("visitor_card_list")

# visitor card update
def visitor_card_update(request, pk):

    card = get_object_or_404(visitor_card, pk=pk)

    if request.method == "POST":

        card.card_color = request.POST["card_color"]
        card.card_access_level = request.POST["card_access_level"]

        card.save()

    return redirect("visitor_card_list")

# visitor card delete
def visitor_card_delete(request, pk):

    card = get_object_or_404(visitor_card, pk=pk)

    if request.method == "POST":
        card.delete()

    return redirect("visitor_card_list")