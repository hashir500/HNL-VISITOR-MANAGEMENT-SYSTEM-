from django.shortcuts import render, redirect, get_object_or_404
from .models import visitor_card, visitor


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
            card_number=request.POST["card_number"],
            card_access_level=request.POST["card_access_level"],
        )

    return redirect("visitor_card_list")

# visitor card update
def visitor_card_update(request, pk):

    card = get_object_or_404(visitor_card, pk=pk)

    if request.method == "POST":

        card.card_color = request.POST["card_color"]
        card.card_number = request.POST["card_number"]
        card.card_access_level = request.POST["card_access_level"]

        card.save()

    return redirect("visitor_card_list")

# visitor card delete
def visitor_card_delete(request, pk):

    card = get_object_or_404(visitor_card, pk=pk)

    if request.method == "POST":
        card.delete()

    return redirect("visitor_card_list")


# visitor list view
def visitor_list(request):
    visitors = visitor.objects.all()

    return render(
        request,
        "visitors/visitor_list.html",
        {
            "visitors": visitors,
        },
    )

# visitor create view
def visitor_create(request):
    if request.method == "POST":
        visitor.objects.create(
            visitor_name=request.POST.get("visitor_name"),
            visitor_email=request.POST.get("visitor_email") or None,
            visitor_phone=request.POST.get("visitor_phone"),
            visitor_address=request.POST.get("visitor_address") or None,
        )

    return redirect("visitor_list")

# visitor update view
def visitor_update(request, visitor_id):
    v = get_object_or_404(visitor, visitor_id=visitor_id)

    if request.method == "POST":
        v.visitor_name = request.POST.get("visitor_name")
        v.visitor_email = request.POST.get("visitor_email") or None
        v.visitor_phone = request.POST.get("visitor_phone")
        v.visitor_address = request.POST.get("visitor_address") or None
        v.save()

    return redirect("visitor_list")


# visitor delete view
def visitor_delete(request, visitor_id):
    v = get_object_or_404(visitor, visitor_id=visitor_id)

    if request.method == "POST":
        v.delete()

    return redirect("visitor_list")