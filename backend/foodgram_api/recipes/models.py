from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(verbose_name='Тэг', max_length=200, unique=True)
    color = models.CharField(verbose_name='Цвет', max_length=7)
    slug = models.SlugField(verbose_name='Slug тэга', unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.slug


class Ingredient(models.Model):
    name = models.CharField(verbose_name='Ингридиент', max_length=256)
    measurement_unit = models.CharField(
        verbose_name='Единица измерения', max_length=128)

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    name = models.CharField(verbose_name='Название рецепта', max_length=256)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор')
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления', validators=[MinValueValidator(1)])
    image = models.ImageField(
        upload_to='recipes/', verbose_name='Картинка')
    tags = models.ManyToManyField(Tag, blank=True)
    ingredients = models.ManyToManyField(Ingredient,
                                         through='IngredientRecipe')
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created',)

    def __str__(self):
        return self.name

    def get_tags(self):
        return '\n'.join([tags.slug for tags in self.tags.all()])

    def get_ingredients(self):
        return '\n'.join(
            [ing.name + ', ' + ing.measurement_unit for ing in
             self.ingredients.all()])


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    amount = models.IntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return f'{self.amount} {self.ingredient_id} {self.recipe_id}'


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='favorite_recipes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='favorited_by')

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite'),
        )


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='cart_items')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='added_to_cart')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_cart')
        ]
