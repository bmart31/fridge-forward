"""SR-2.3: dummy data for checking that suggestions stay fast.

Used by `python manage.py benchmark_suggestions` and by PerformanceTests.
"""
import random

from .models import Ingredient, PantryItem, Recipe

METHOD = (
    "Prepare all the ingredients. Combine them in a large bowl. "
    "Cook over a medium heat for ten minutes, stirring often. Season and serve."
)


def create_dummy_recipes(count=1000, pool_size=60, pantry_size=30, seed=0):
    """Create `count` recipes using 2-6 ingredients each from a pool of
    `pool_size` dummy ingredients, and put the first `pantry_size` of those
    ingredients in the pantry, so that some recipes match and most don't.

    Uses bulk inserts, so it only takes a few queries. Returns the number of
    dummy recipes that can be made.
    """
    rng = random.Random(seed)

    Ingredient.objects.bulk_create(
        [Ingredient(name=f"dummy ingredient {i:03}") for i in range(pool_size)],
        ignore_conflicts=True,
    )
    pool = list(Ingredient.objects.filter(name__startswith="dummy ingredient ").order_by("name"))
    in_pantry = pool[:pantry_size]
    PantryItem.objects.bulk_create(
        [PantryItem(ingredient=i) for i in in_pantry], ignore_conflicts=True,
    )

    recipes = Recipe.objects.bulk_create(
        [Recipe(name=f"Dummy recipe {n:04}", instructions=METHOD) for n in range(count)]
    )
    Through = Recipe.ingredients.through
    links, makeable = [], 0
    have = {i.pk for i in in_pantry}
    for recipe in recipes:
        chosen = rng.sample(pool, rng.randint(2, 6))
        links += [Through(recipe_id=recipe.pk, ingredient_id=i.pk) for i in chosen]
        makeable += {i.pk for i in chosen} <= have
    Through.objects.bulk_create(links)
    return makeable
