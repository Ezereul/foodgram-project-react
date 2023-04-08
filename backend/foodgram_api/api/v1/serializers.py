from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (ShoppingCart, FavoriteRecipe, Ingredient, IngredientRecipe,
                            Recipe, Tag)
from users.models import Subscribtion

from .paginators import SubRecipePagination
from .utils import create_recipeingredient

User = get_user_model()
# TODO: review

class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(validators=[validate_password],
                                         required=True)
    current_password = serializers.CharField(required=True)

    def validate_current_password(self, current_password):
        current_user = self.context['request'].user
        if not check_password(current_password, current_user.password):
            raise serializers.ValidationError('Неверный текущий пароль')
        return current_password


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


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = IngredientRecipeSerializer(many=True,
                                             source='ingredientrecipe_set')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)

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
            return ShoppingCart.objects.filter(recipe=obj, user=current_user).exists()
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
                                              queryset=Tag.objects.all())
    author = UserSerializer(default=serializers.CurrentUserDefault())
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients', 'name', 'image',
                  'text', 'cooking_time', 'author')

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data

    @transaction.atomic
    def create(self, validated_data):
        recipe = create_recipeingredient(validated_data)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        create_recipeingredient(validated_data, instance, update=True)

        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.save()

        return instance


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

    def validate_id(self, id):
        if id == self.context['request'].user.id:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя')
        return id
