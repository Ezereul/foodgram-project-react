from django.contrib import admin
from django.contrib.auth import get_user_model

from recipes.models import Tag, Recipe, Ingredient

User = get_user_model()

class TagInLine(admin.TabularInline):
    model = Recipe.tags.through


class IngredientInLine(admin.TabularInline):
    model = Recipe.ingredients.through


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (TagInLine, IngredientInLine)
    list_display = ('name', 'author')
    list_filter = ('name', 'author', 'tags')
    readonly_fields = ('in_favorite',)

    def in_favorite(self, obj):
        count = obj.favorited_by.count()
        return f'Количество добавлений в избранное: {count}'



@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)

