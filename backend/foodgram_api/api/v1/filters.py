from django_filters import FilterSet, BooleanFilter, CharFilter, NumberFilter, \
    AllValuesMultipleFilter
from rest_framework.exceptions import ValidationError

from recipes.models import Recipe


class RecipeFilter(FilterSet):
    is_favorited = CharFilter(field_name='is_favorited', method='filter_is_favorited')
    is_in_shopping_cart = CharFilter(
        method='filter_is_in_shopping_cart')
    author = NumberFilter(field_name='author_id')
    tags = AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('author', 'tags')

    def filter_is_favorited(self, queryset, name, value):
        value = int(value)
        if value not in [0, 1]:
            raise ValidationError(f'Значение {name} должно быть 0 или 1')
        user = self.request.user
        if user.is_anonymous:
            return Recipe.objects.none()
        if value == 1:
            return queryset.filter(favorited_by__user=user)
        return queryset.exclude(favorited_by__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        value = int(value)
        if value not in (0, 1):
            raise ValidationError(f'Значение {name} должно быть 0 или 1')
        user = self.request.user
        if user.is_anonymous:
            return Recipe.objects.none()
        if value == 1:
            return queryset.filter(added_to_cart__user=user)
        return queryset.exclude(added_to_cart__user=user)


