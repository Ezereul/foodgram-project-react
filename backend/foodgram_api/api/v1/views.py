import io

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (FavoriteRecipe, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Tag)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from users.models import Subscribtion
from .constants import X_FOR_PDF_FILE, Y_FOR_PDF_FILE
from .filters import RecipeFilter
from .mixins import RetrieveListViewSet
from .paginators import ProjectPagination
from .permissions import IsAdminOrAuthorOrReadOnly
from .serializers import (CreateUpdateRecipeSerializer, FavoriteCartSerializer,
                          IngredientSerializer, RecipeSerializer,
                          ShortRecipeSerializer, SubscribeSerializer,
                          TagSerializer, UserSerializer,
                          ValidateSubscriptionSerializer)

User = get_user_model()
BASE_DIR = settings.BASE_DIR


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(methods=['POST', 'DELETE'],
            permission_classes=(IsAuthenticated,),
            detail=True)
    def subscribe(self, request, pk):
        subscribe_to = self.get_object()
        context = {'subscribe_to': subscribe_to,
                   'request': request}
        serializer_to_validate = ValidateSubscriptionSerializer(
            data=request.data, context=context)
        serializer_to_validate.is_valid(raise_exception=True)
        serializer_to_create = SubscribeSerializer(
            subscribe_to, context={'request': request})

        if request.method == 'POST':
            Subscribtion.objects.create(
                subscriber=request.user, subscribed_to=subscribe_to)
            return Response(data=serializer_to_create.data,
                            status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            Subscribtion.objects.get(subscriber=request.user,
                                     subscribed_to_id=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET'],
            permission_classes=(IsAuthenticated,),
            detail=False,)
    def subscriptions(self, request):
        queryset = User.objects.filter(
            subscribing__subscriber=self.request.user)
        paginator = ProjectPagination()
        subscriptions = paginator.paginate_queryset(queryset, request)
        serializer = SubscribeSerializer(subscriptions, many=True,
                                         context={'request': request})
        return paginator.get_paginated_response(serializer.data)


class TagViewSet(RetrieveListViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(RetrieveListViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    filterset_fields = ('author', 'tags')
    permission_classes = (IsAuthenticatedOrReadOnly, IsAdminOrAuthorOrReadOnly)

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return CreateUpdateRecipeSerializer
        return RecipeSerializer

    @action(methods=['POST', 'DELETE'],
            detail=True,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        recipe = self.get_object()
        context = {'action': 'favorite', 'user': request.user,
                   'recipe': recipe, 'method': request.method}
        to_validate = FavoriteCartSerializer(data=request.data,
                                             context=context)
        to_validate.is_valid(raise_exception=True)
        serializer = ShortRecipeSerializer(recipe)

        if request.method == 'POST':
            FavoriteRecipe.objects.get_or_create(
                recipe=recipe, user=request.user)
            return Response(
                data=serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            FavoriteRecipe.objects.get(recipe=recipe,
                                       user=request.user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST', 'DELETE'],
            detail=True,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        recipe = self.get_object()
        context = {'action': 'shopping_cart', 'user': request.user,
                   'recipe': recipe, 'method': request.method}
        to_validate = FavoriteCartSerializer(data=request.data,
                                             context=context)
        to_validate.is_valid(raise_exception=True)
        to_create = ShortRecipeSerializer(recipe)

        if request.method == 'POST':
            ShoppingCart.objects.create(recipe=recipe, user=request.user)
            return Response(
                data=to_create.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            ShoppingCart.objects.get(recipe=recipe, user=request.user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET'],
            detail=False,
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        current_user = request.user
        recipes = Recipe.objects.filter(added_to_cart__user=current_user)
        ingredients = IngredientRecipe.objects.filter(
            recipe__in=recipes).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))

        buffer = io.BytesIO()
        pdfmetrics.registerFont(TTFont(
            'Bitter',
            BASE_DIR / 'Bitter-VariableFont_wght.ttf'))
        pdf = canvas.Canvas(buffer)
        pdf.setFont('Bitter', 12)

        y = Y_FOR_PDF_FILE
        x = X_FOR_PDF_FILE
        for ingredient in ingredients:
            text = (f'{ingredient["ingredient__name"]} - '
                    f' {ingredient["total_amount"]}'
                    f'{ingredient["ingredient__measurement_unit"]}')
            pdf.drawString(x, y, text)
            y -= 10
            if y == 0:
                x += 250
                y = 800

        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        filename = (f'{current_user}_shopping_cart.pdf')
        response = FileResponse(buffer, as_attachment=True, filename=filename,
                                status=status.HTTP_200_OK)

        return response
