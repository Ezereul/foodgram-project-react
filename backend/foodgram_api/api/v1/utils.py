from rest_framework import serializers

from recipes.models import IngredientRecipe, Ingredient, Recipe


def create_recipeingredient(validated_data, recipe=None, update=False):
    ingredients_data = validated_data.pop('ingredientrecipe_set')
    tags_data = validated_data.pop('tags')
    print(validated_data)
    if update:
        IngredientRecipe.objects.filter(recipe=recipe).delete()
    else:
        recipe = Recipe.objects.create(**validated_data)
    for ingredient_data in ingredients_data:
        ingredient_id = ingredient_data['ingredient']['id']
        ingredient_amount = ingredient_data['amount']
        try:
            ingredient = Ingredient.objects.get(id=ingredient_id)
        except Ingredient.DoesNotExist:
            raise serializers.ValidationError(
                f'Ingredient with id={ingredient_id} does not exist')
        IngredientRecipe.objects.create(
            recipe=recipe, ingredient=ingredient, amount=ingredient_amount)

    recipe.tags.set(tags_data)
    if not update:
        return recipe
