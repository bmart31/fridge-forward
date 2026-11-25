from django.db import migrations

# The starter recipes in 0002 used plural names. Recipe data uses singular,
# lowercase names (SCRUM-52) so that matching lines up across the dataset.
RENAMES = {"eggs": "egg", "tomatoes": "tomato"}


def singularise(apps, schema_editor):
    Ingredient = apps.get_model("pantry", "Ingredient")
    PantryItem = apps.get_model("pantry", "PantryItem")
    for old, new in RENAMES.items():
        src = Ingredient.objects.filter(name=old).first()
        if src is None:
            continue
        dst = Ingredient.objects.filter(name=new).first()
        if dst is None:
            src.name = new
            src.save()
            continue
        # Both forms exist: merge the plural into the singular.
        for recipe in src.recipes.all():
            recipe.ingredients.add(dst)
        item = PantryItem.objects.filter(ingredient=src).first()
        if item and not PantryItem.objects.filter(ingredient=dst).exists():
            item.ingredient = dst
            item.save()
        src.delete()


class Migration(migrations.Migration):
    dependencies = [("pantry", "0002_seed_recipes")]
    operations = [migrations.RunPython(singularise, migrations.RunPython.noop)]
