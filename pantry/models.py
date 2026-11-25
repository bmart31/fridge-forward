import re

from django.db import models


def normalise(name):
    return name.strip().lower()


class IngredientManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=normalise(name))


class Ingredient(models.Model):
    """An ingredient name. Shared by the pantry and recipes."""
    name = models.CharField(max_length=100, unique=True)

    objects = IngredientManager()

    def natural_key(self):
        # Lets fixtures refer to ingredients by name, e.g. ["egg"], not by id.
        return (self.name,)

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

    def steps(self):
        """SR-2.4: the method split into steps, one per line or sentence."""
        return [
            s.strip()
            for line in self.instructions.splitlines()
            for s in re.split(r"(?<=[.!?])\s+", line)
            if s.strip()
        ]

    def __str__(self):
        return self.name
