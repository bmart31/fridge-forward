from django.db.models import Count, F, Q

from .models import PantryItem, Recipe


def makeable_recipes():
    """KUR-02 / KUR-03: only recipes whose every ingredient is in the pantry.

    SR-2.3: matching runs in the database. Each recipe's ingredients are
    counted, along with how many of those are in the pantry, and a recipe is
    kept only when the two numbers are equal. Only the matching recipes are
    fetched, and their ingredients are prefetched, so this always takes at
    most 2 queries however many recipes exist.

    Returns an empty list if nothing matches.
    """
    have = PantryItem.objects.values("ingredient_id")
    return list(
        Recipe.objects.annotate(
            needed=Count("ingredients", distinct=True),
            matched=Count("ingredients", filter=Q(ingredients__in=have), distinct=True),
        )
        .filter(needed__gt=0, matched=F("needed"))
        .order_by("name", "pk")
        .prefetch_related("ingredients")
    )
