from django_filters import (AllValuesMultipleFilter, BooleanFilter, FilterSet,
                            NumberFilter)

from recipes.models import Recipe


class RecipeFilter(FilterSet):
    is_favorited = BooleanFilter(field_name='is_favorited')
    is_in_shopping_cart = BooleanFilter(field_name='is_in_shopping_cart')
    author = NumberFilter(field_name='author_id')
    tags = AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')
