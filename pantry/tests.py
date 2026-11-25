from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Ingredient, PantryItem, Recipe
from .services import makeable_recipes


def make_recipe(name, *ingredients):
    r = Recipe.objects.create(name=name)
    r.ingredients.set([Ingredient.objects.get_or_create(name=i)[0] for i in ingredients])
    return r


class AddIngredientTests(TestCase):
    def test_add_comma_separated_and_normalised(self):  # KUR-01, KUR-04
        self.client.post(reverse("add_ingredient"), {"names": " Eggs , milk,,eggs"})
        self.assertEqual(
            sorted(PantryItem.objects.values_list("ingredient__name", flat=True)),
            ["eggs", "milk"],
        )

    def test_remove(self):
        self.client.post(reverse("add_ingredient"), {"names": "eggs"})
        item = PantryItem.objects.get()
        self.client.post(reverse("remove_ingredient", args=[item.pk]))
        self.assertFalse(PantryItem.objects.exists())


class MatchingTests(TestCase):
    def setUp(self):
        self.omelette = make_recipe("Omelette", "eggs", "butter")
        self.toast = make_recipe("Cheese toast", "bread", "cheese")

    def have(self, *names):
        for n in names:
            PantryItem.objects.create(ingredient=Ingredient.objects.get_or_create(name=n)[0])

    def test_only_fully_makeable_recipes(self):  # KUR-02, KUR-03
        self.have("eggs", "butter", "bread")
        self.assertEqual(makeable_recipes(), [self.omelette])

    def test_no_match_returns_nothing(self):  # KUR-03
        self.have("eggs")
        self.assertEqual(makeable_recipes(), [])
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, "No recipes match")


class RecipeFixtureTests(TestCase):
    """SCRUM-52: the recipe dataset in pantry/fixtures/recipes.json."""

    def setUp(self):
        call_command("loaddata", "recipes", verbosity=0)

    def test_at_least_25_recipes(self):
        self.assertGreaterEqual(Recipe.objects.count(), 25)

    def test_every_recipe_is_complete(self):
        for recipe in Recipe.objects.prefetch_related("ingredients"):
            with self.subTest(recipe=recipe.name):
                self.assertTrue(recipe.name.strip())
                self.assertTrue(recipe.instructions.strip())
                self.assertGreaterEqual(recipe.ingredients.count(), 1)

    def test_ingredient_names_are_normalised(self):
        for name in Ingredient.objects.values_list("name", flat=True):
            self.assertEqual(name, name.strip().lower())

    def test_some_recipes_need_only_a_few_ingredients(self):
        short = [r for r in Recipe.objects.prefetch_related("ingredients") if r.ingredients.count() <= 3]
        self.assertGreaterEqual(len(short), 5)

    def test_loading_twice_does_not_duplicate(self):
        recipes, ingredients = Recipe.objects.count(), Ingredient.objects.count()
        call_command("loaddata", "recipes", verbosity=0)
        self.assertEqual(Recipe.objects.count(), recipes)
        self.assertEqual(Ingredient.objects.count(), ingredients)

    def test_fixture_recipes_match_a_pantry(self):  # KUR-02 with real data
        for n in ["bread", "cheese"]:
            PantryItem.objects.create(ingredient=Ingredient.objects.get(name=n))
        self.assertIn("Cheese toast", [r.name for r in makeable_recipes()])


class SingularSeedTests(TestCase):
    def test_seed_ingredients_are_singular(self):  # migration 0003
        names = set(Ingredient.objects.values_list("name", flat=True))
        self.assertTrue({"egg", "tomato"} <= names)
        self.assertFalse({"eggs", "tomatoes"} & names)
