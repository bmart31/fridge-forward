from .models import PantryItem, Recipe


def makeable_recipes():
    """KUR-02 / KUR-03: only recipes whose every ingredient is in the pantry.

    Returns an empty list if nothing matches.
    """
    have = set(PantryItem.objects.values_list("ingredient_id", flat=True))
    results = []
    for recipe in Recipe.objects.prefetch_related("ingredients"):
        needed = {i.id for i in recipe.ingredients.all()}
        if needed and needed <= have:
            results.append(recipe)
    return results
