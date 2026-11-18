from django.db import migrations

RECIPES = {
    "Scrambled eggs": (["eggs", "butter", "salt"], "Whisk eggs, cook gently in butter, season."),
    "Cheese toast": (["bread", "cheese"], "Put cheese on bread, grill until bubbling."),
    "Omelette": (["eggs", "butter", "cheese"], "Beat eggs, cook in butter, add cheese, fold."),
    "Pasta with tomato sauce": (["pasta", "tomatoes", "garlic", "olive oil"], "Boil pasta. Fry garlic in oil, add tomatoes, simmer, toss."),
    "Pancakes": (["flour", "eggs", "milk", "butter"], "Whisk flour, eggs, milk. Fry in butter."),
    "Banana smoothie": (["banana", "milk"], "Blend."),
    "Fried rice": (["rice", "eggs", "soy sauce", "onion"], "Fry onion, add rice, push aside, scramble eggs, add soy sauce."),
}


def seed(apps, schema_editor):
    Ingredient = apps.get_model("pantry", "Ingredient")
    Recipe = apps.get_model("pantry", "Recipe")
    for name, (ingredients, instructions) in RECIPES.items():
        recipe = Recipe.objects.create(name=name, instructions=instructions)
        recipe.ingredients.set([Ingredient.objects.get_or_create(name=i)[0] for i in ingredients])


def unseed(apps, schema_editor):
    apps.get_model("pantry", "Recipe").objects.filter(name__in=RECIPES).delete()


class Migration(migrations.Migration):
    dependencies = [("pantry", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
