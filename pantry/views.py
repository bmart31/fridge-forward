from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .models import Ingredient, PantryItem, normalise
from .services import makeable_recipes


def page_context():
    # SR-2.5: built fresh on every request, so suggestions always match the
    # pantry as it is right now. Nothing here is cached.
    return {
        "pantry": PantryItem.objects.select_related("ingredient").order_by("ingredient__name"),
        "recipes": makeable_recipes(),
        "known_ingredients": Ingredient.objects.order_by("name"),
    }


def after_change(request):
    """SR-2.5: what add/remove return once the pantry has changed.

    HTMX requests get just the fridge list and suggestions, which HTMX swaps
    into the page. Normal form posts are redirected back to the home page
    (Post/Redirect/Get), which recalculates everything.
    """
    if request.headers.get("HX-Request"):
        return render(request, "pantry/_fridge_and_suggestions.html", page_context())
    return redirect("home")


@never_cache  # SR-2.5: the back button must not show out-of-date suggestions
def home(request):
    return render(request, "pantry/home.html", page_context())


@require_POST
def add_ingredient(request):
    # KUR-04: one text box; comma-separated lets you add several at once.
    raw = request.POST.get("names", "")
    for name in raw.split(","):
        name = normalise(name)
        if name:
            ingredient, _ = Ingredient.objects.get_or_create(name=name)
            PantryItem.objects.get_or_create(ingredient=ingredient)
    return after_change(request)


@require_POST
def remove_ingredient(request, pk):
    get_object_or_404(PantryItem, pk=pk).delete()
    return after_change(request)
