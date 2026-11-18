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
