from recipes.models import Ingredient, IngredientRecipe, Recipe
from rest_framework import serializers


def create_recipeingredient(validated_data, recipe=None, update=False):
    ingredients_data = validated_data.pop('ingredientrecipe_set')
    tags_data = validated_data.pop('tags')
    print(validated_data)
    if update:
        IngredientRecipe.objects.filter(recipe=recipe).delete()
    else:
        recipe = Recipe.objects.create(**validated_data)
    ingredients_to_create = []
    for ingredient_data in ingredients_data:
        ingredient_id = ingredient_data['ingredient']['id']
        ingredient_amount = ingredient_data['amount']
        try:
            ingredient = Ingredient.objects.get(id=ingredient_id)
        except Ingredient.DoesNotExist:
            raise serializers.ValidationError(
                f'Ingredient with id={ingredient_id} does not exist')
        ingredient_recipe = IngredientRecipe(
            recipe=recipe, ingredient=ingredient, amount=ingredient_amount)
        ingredients_to_create.append(ingredient_recipe)

    if ingredients_to_create:
        IngredientRecipe.objects.bulk_create(ingredients_to_create)

    recipe.tags.set(tags_data)
    if not update:
        return recipe
