from django.contrib import admin

from .models import Ingredient, PantryItem, Recipe

admin.site.register(Ingredient)
admin.site.register(PantryItem)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    filter_horizontal = ("ingredients",)
