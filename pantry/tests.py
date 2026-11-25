import time
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .benchmark import create_dummy_recipes
from .models import Ingredient, PantryItem, Recipe
from .services import makeable_recipes


def make_recipe(name, *ingredients):
    r = Recipe.objects.create(name=name)
    r.ingredients.set([Ingredient.objects.get_or_create(name=i)[0] for i in ingredients])
    return r


class AddIngredientTests(TestCase):
    def test_home_has_visible_ingredient_label(self):
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, '<label for="ingredient-input">Add an ingredient</label>', html=True)

    def test_add_one_item(self):  # KUR-01, KUR-04
        self.client.post(reverse("add_ingredient"), {"names": "  Egg  "})
        self.assertEqual(
            list(PantryItem.objects.values_list("ingredient__name", flat=True)),
            ["egg"],
        )

    def test_add_comma_separated_and_normalised(self):  # KUR-01, KUR-04
        self.client.post(reverse("add_ingredient"), {"names": " Eggs , milk,,eggs"})
        self.assertEqual(
            sorted(PantryItem.objects.values_list("ingredient__name", flat=True)),
            ["eggs", "milk"],
        )

    def test_empty_input_is_rejected(self):
        for raw in ("", "   ", ", , "):
            with self.subTest(raw=raw):
                resp = self.client.post(reverse("add_ingredient"), {"names": raw}, follow=True)
                self.assertFalse(PantryItem.objects.exists())
                self.assertContains(resp, "Please enter at least one ingredient.")

    def test_remove(self):
        self.client.post(reverse("add_ingredient"), {"names": "eggs"})
        item = PantryItem.objects.get()
        self.client.post(reverse("remove_ingredient", args=[item.pk]))
        self.assertFalse(PantryItem.objects.exists())


class MatchingTests(TestCase):
    """SCRUM-53: makeable_recipes() compares the pantry against each recipe.

    Test names carry SR-2.2 (recipe matching) / SR-3.1 (only makeable
    recipes shown) so they can be traced back to the requirements.
    """

    def setUp(self):
        # Migration 0002 seeds real recipes; remove them so each test
        # controls exactly which recipes exist.
        Recipe.objects.all().delete()
        self.omelette = make_recipe("Omelette", "egg", "butter")
        self.toast = make_recipe("Cheese toast", "bread", "cheese")

    def have(self, *names):
        for n in names:
            PantryItem.objects.create(ingredient=Ingredient.objects.get_or_create(name=n)[0])

    def names(self):
        return sorted(r.name for r in makeable_recipes())

    def test_sr_2_2_sr_3_1_all_ingredients_returns_recipe(self):
        self.have("egg", "butter")
        self.assertEqual(makeable_recipes(), [self.omelette])

    def test_sr_2_2_sr_3_1_missing_one_ingredient_excludes_recipe(self):
        self.have("egg")  # no butter
        self.assertEqual(makeable_recipes(), [])

    def test_sr_2_2_extra_ingredients_still_returns_recipe(self):
        self.have("egg", "butter", "milk", "onion")
        self.assertEqual(makeable_recipes(), [self.omelette])

    def test_sr_2_2_sr_3_1_empty_pantry_returns_nothing(self):
        self.assertEqual(makeable_recipes(), [])

    def test_sr_2_2_sr_3_1_only_makeable_subset_returned(self):
        make_recipe("Pancakes", "egg", "milk", "flour")
        make_recipe("Buttered toast", "bread", "butter")
        self.have("egg", "butter", "bread")
        self.assertEqual(self.names(), ["Buttered toast", "Omelette"])

    def test_sr_3_1_no_match_shows_message_on_home(self):
        self.have("egg")
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, "No recipes match")


class SuggestionsUpdateTests(TestCase):
    """SCRUM-56 / SR-2.5: suggestions update straight after add/remove."""

    CARD = "<h3>Cheese toast</h3>"

    def setUp(self):
        Recipe.objects.all().delete()
        make_recipe("Cheese toast", "bread", "cheese")
        PantryItem.objects.create(ingredient=Ingredient.objects.get(name="bread"))

    def add(self, names, **headers):
        return self.client.post(reverse("add_ingredient"), {"names": names}, **headers)

    def remove(self, name, **headers):
        item = PantryItem.objects.get(ingredient__name=name)
        return self.client.post(reverse("remove_ingredient", args=[item.pk]), **headers)

    def test_sr_2_5_add_last_missing_ingredient_recipe_appears(self):
        self.assertNotContains(self.client.get(reverse("home")), self.CARD, html=True)
        resp = self.add("cheese")
        self.assertRedirects(resp, reverse("home"))
        self.assertContains(self.client.get(resp.url), self.CARD, html=True)

    def test_sr_2_5_remove_ingredient_recipe_disappears(self):
        self.add("cheese")
        self.assertContains(self.client.get(reverse("home")), self.CARD, html=True)
        resp = self.remove("cheese")
        self.assertRedirects(resp, reverse("home"))
        page = self.client.get(resp.url)
        self.assertNotContains(page, self.CARD, html=True)
        self.assertContains(page, "No recipes match")

    def test_sr_2_5_htmx_add_returns_updated_suggestions_without_full_page(self):
        resp = self.add("cheese", HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "pantry/_fridge_and_suggestions.html")
        self.assertTemplateNotUsed(resp, "pantry/home.html")
        self.assertContains(resp, self.CARD, html=True)
        self.assertContains(resp, 'aria-label="Remove cheese"')

    def test_sr_2_5_htmx_remove_returns_updated_suggestions(self):
        self.add("cheese")
        resp = self.remove("cheese", HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, self.CARD, html=True)
        self.assertContains(resp, "No recipes match")

    def test_sr_2_5_home_page_is_never_cached(self):
        cache_control = self.client.get(reverse("home"))["Cache-Control"]
        for directive in ("no-cache", "no-store", "max-age=0"):
            self.assertIn(directive, cache_control)

    def test_sr_2_5_forms_work_without_javascript(self):
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, f'action="{reverse("add_ingredient")}"')
        item = PantryItem.objects.get()
        self.assertContains(resp, f'action="{reverse("remove_ingredient", args=[item.pk])}"')


class PerformanceTests(TestCase):
    """SCRUM-54 / SR-2.3: suggestions stay fast with a large recipe database."""

    # pantry list + matching recipes + their ingredients + autocomplete list
    HOME_QUERIES = 4

    def test_sr_2_3_query_count_does_not_grow_with_recipes(self):
        PantryItem.objects.create(ingredient=Ingredient.objects.get(name="bread"))
        PantryItem.objects.create(ingredient=Ingredient.objects.get(name="cheese"))
        make_recipe("Cheese toast", "bread", "cheese")
        with self.assertNumQueries(2):
            makeable_recipes()
        with self.assertNumQueries(self.HOME_QUERIES):
            self.client.get(reverse("home"))

        create_dummy_recipes(1000)
        with self.assertNumQueries(2):
            makeable_recipes()
        with self.assertNumQueries(self.HOME_QUERIES):
            self.client.get(reverse("home"))

    def test_sr_2_3_home_page_with_1000_recipes_under_2_seconds(self):
        expected = create_dummy_recipes(1000)
        start = time.perf_counter()
        resp = self.client.get(reverse("home"))
        elapsed = time.perf_counter() - start
        self.assertEqual(resp.status_code, 200)
        self.assertLess(elapsed, 2.0)
        dummy = [r for r in resp.context["recipes"] if r.name.startswith("Dummy recipe")]
        self.assertGreater(expected, 0)
        self.assertEqual(len(dummy), expected)

    def test_sr_2_3_benchmark_command_runs_and_rolls_back(self):
        before = Recipe.objects.count()
        out = StringIO()
        call_command("benchmark_suggestions", recipes=200, runs=1, stdout=out)
        self.assertIn("PASS", out.getvalue())
        self.assertEqual(Recipe.objects.count(), before)


class RecipeCardTests(TestCase):
    """SCRUM-55 / SR-2.4: each suggestion shows its name, ingredients and method."""

    def setUp(self):
        Recipe.objects.all().delete()
        self.toast = make_recipe("Cheese toast", "bread", "cheese")
        self.toast.instructions = "Toast the bread. Add the cheese! Grill until bubbling."
        self.toast.save()
        make_recipe("Jam toast", "bread", "jam")  # makeable, no method
        for n in ["bread", "cheese", "jam"]:
            PantryItem.objects.create(ingredient=Ingredient.objects.get(name=n))

    def test_sr_2_4_steps_split_on_sentences_and_lines(self):
        self.assertEqual(
            self.toast.steps(),
            ["Toast the bread.", "Add the cheese!", "Grill until bubbling."],
        )
        self.assertEqual(Recipe(instructions="Mix.\n\nBake for 1.5 hours").steps(), ["Mix.", "Bake for 1.5 hours"])
        self.assertEqual(Recipe(instructions="  ").steps(), [])

    def test_sr_2_4_card_shows_name_ingredients_and_numbered_method(self):
        resp = self.client.get(reverse("home"))
        self.assertTemplateUsed(resp, "pantry/_recipe_card.html")
        self.assertContains(resp, "<h3>Cheese toast</h3>", html=True)
        self.assertContains(resp, "<ul><li>bread</li><li>cheese</li></ul>", html=True)
        self.assertContains(
            resp,
            "<ol><li>Toast the bread.</li><li>Add the cheese!</li><li>Grill until bubbling.</li></ol>",
            html=True,
        )

    def test_sr_2_4_method_collapsed_behind_details(self):
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, "<summary>Show method</summary>", count=2, html=True)
        self.assertNotContains(resp, "<details open")

    def test_sr_2_4_every_suggestion_has_all_three_parts(self):
        resp = self.client.get(reverse("home"))
        html = resp.content.decode()
        cards = html.split('<article class="recipe-card">')[1:]
        self.assertEqual(len(cards), len(resp.context["recipes"]))
        for card in cards:
            with self.subTest(card=card[:40]):
                self.assertIn("<h3>", card)
                self.assertIn("<h4>Ingredients</h4>", card)
                self.assertIn("<summary>Show method</summary>", card)
        self.assertContains(resp, "No method written yet.")  # Jam toast

    def test_sr_2_4_page_has_mobile_viewport(self):
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, 'name="viewport" content="width=device-width, initial-scale=1"')


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
