from typing import Union

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (FavoriteRecipe, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Tag)
from rest_framework import serializers

from users.models import Subscribtion
from .paginators import SubRecipePagination

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True,
                                     validators=[validate_password])

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'password')

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user
        if current_user.is_authenticated:
            return Subscribtion.objects.filter(
                subscriber=current_user, subscribed_to=obj).exists()
        return False


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    amount = serializers.IntegerField()
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateUpdateIngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')

    def validate(self, attrs):
        if attrs['amount'] < 1:
            raise serializers.ValidationError('Количество не может быть '
                                              'отрицательным')
        return attrs


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = IngredientRecipeSerializer(many=True,
                                             source='ingredientrecipe_set')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def get_is_favorited(self, obj):
        current_user = self.context['request'].user
        if current_user.is_authenticated:
            return FavoriteRecipe.objects.filter(recipe=obj,
                                                 user=current_user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        current_user = self.context['request'].user
        if current_user.is_authenticated:
            return ShoppingCart.objects.filter(recipe=obj,
                                               user=current_user).exists()
        return False


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CreateUpdateRecipeSerializer(serializers.ModelSerializer):
    ingredients = CreateUpdateIngredientRecipeSerializer(
        many=True, source='ingredientrecipe_set')
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all(),
                                              required=True, allow_empty=False)
    author = UserSerializer(default=serializers.CurrentUserDefault())
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients', 'name', 'image',
                  'text', 'cooking_time', 'author')

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Ингредиенты не добавлены')
        ingredients_uniq_ids = []
        for ingredient_obj in value:
            id = ingredient_obj['ingredient']['id']
            if id not in ingredients_uniq_ids:
                ingredients_uniq_ids.append(id)
            else:
                raise serializers.ValidationError('Ингредиент уже добавлен')
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Обязательное поле')
        return value

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data

    @transaction.atomic
    def create(self, validated_data):
        recipe = self.create_recipeingredient(validated_data)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        self.create_recipeingredient(validated_data, instance, update=True)

        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.save()

        return instance

    def create_recipeingredient(self, validated_data: dict,
                                recipe: Recipe = None,
                                update: bool = False) -> Union[Recipe, None]:
        ingredients_data = validated_data.pop('ingredientrecipe_set')
        tags_data = validated_data.pop('tags')
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

        IngredientRecipe.objects.bulk_create(ingredients_to_create)

        recipe.tags.set(tags_data)
        if not update:
            return recipe


class SubscribeSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author_id=obj.id).count()

    def get_recipes(self, obj):
        paginator = SubRecipePagination()
        limit = self.context['request'].query_params.get('recipes_limit', 3)
        paginator.page_size = limit
        queryset = obj.recipes.all()
        page = paginator.paginate_queryset(queryset, self.context['request'])
        serializer = ShortRecipeSerializer(page, many=True)
        return serializer.data


class ValidateSubscriptionSerializer(serializers.Serializer):
    def validate(self, attrs):
        subscriber = self.context['request'].user
        subscribe_to = self.context['subscribe_to']
        method = self.context['request'].method

        if subscriber == subscribe_to:
            raise serializers.ValidationError(
                'Вы не можете подписаться или отписаться от самого себя')
        if method == 'POST':
            if Subscribtion.objects.filter(
                    subscriber=subscriber,
                    subscribed_to=subscribe_to).exists():
                raise serializers.ValidationError('Вы уже подписаны')
        elif method == 'DELETE':
            if not Subscribtion.objects.filter(
                    subscriber=subscriber,
                    subscribed_to=subscribe_to).exists():
                raise serializers.ValidationError('Вы не подписаны')

        return attrs


class FavoriteCartSerializer(serializers.Serializer):
    def validate(self, attrs):
        action = self.context['action']
        user = self.context['user']
        recipe = self.context['recipe']
        method = self.context['method']
        favorited = FavoriteRecipe.objects.filter(
            recipe=recipe, user=user).exists()
        in_cart = ShoppingCart.objects.filter(
            recipe=recipe, user=user).exists()

        if action == 'favorite':
            if method == 'POST' and favorited:
                raise serializers.ValidationError('Уже добавлен в избранное')
            elif method == 'DELETE' and not favorited:
                raise serializers.ValidationError('Не в избранном')
        elif action == 'shopping_cart':
            if method == 'POST' and in_cart:
                raise serializers.ValidationError('Уже в корзине')
            elif method == 'DELETE' and not in_cart:
                raise serializers.ValidationError('Не в корзине')

        return attrs
