from django.db import models


def normalise(name):
    return name.strip().lower()


class Ingredient(models.Model):
    """An ingredient name. Shared by the pantry and recipes."""
    name = models.CharField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        self.name = normalise(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PantryItem(models.Model):
    """KUR-01: an ingredient the user currently has. (Single user for now.)"""
    ingredient = models.OneToOneField(Ingredient, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ingredient.name


class Recipe(models.Model):
    name = models.CharField(max_length=200)
    ingredients = models.ManyToManyField(Ingredient, related_name="recipes")
    instructions = models.TextField(blank=True)

    def __str__(self):
        return self.name
