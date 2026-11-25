from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Ingredient, PantryItem, normalise
from .services import makeable_recipes


def home(request):
    return render(request, "pantry/home.html", {
        "pantry": PantryItem.objects.select_related("ingredient").order_by("ingredient__name"),
        "recipes": makeable_recipes(),
        "known_ingredients": Ingredient.objects.order_by("name"),
    })


@require_POST
def add_ingredient(request):
    # KUR-04: one text box; comma-separated lets you add several at once.
    raw = request.POST.get("names", "")
    names = [name for name in (normalise(part) for part in raw.split(",")) if name]
    if not names:
        messages.error(request, "Please enter at least one ingredient.")
        return redirect("home")

    for name in names:
        ingredient, _ = Ingredient.objects.get_or_create(name=name)
        PantryItem.objects.get_or_create(ingredient=ingredient)
    return redirect("home")


@require_POST
def remove_ingredient(request, pk):
    get_object_or_404(PantryItem, pk=pk).delete()
    return redirect("home")
