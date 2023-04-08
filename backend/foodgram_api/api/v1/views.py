import io

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from django.conf import settings

from recipes.models import (ShoppingCart, FavoriteRecipe, Ingredient, IngredientRecipe,
                            Recipe, Tag)
from users.models import Subscribtion

from .filters import RecipeFilter
from .paginators import ProjectPagination
from .permissions import IsAdminOrAuthorOrReadOnly
from .serializers import (CreateUpdateRecipeSerializer, IngredientSerializer,
                          RecipeSerializer, SetPasswordSerializer,
                          ShortRecipeSerializer, SubscribeSerializer,
                          TagSerializer, UserSerializer)

User = get_user_model()
# TODO: review
BASE_DIR = settings.BASE_DIR


class RetrieveListViewSet(mixins.RetrieveModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    pass


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        serializer.save(password=make_password(
            self.request.data.get('password')))

    @action(methods=['POST'],
            permission_classes=(IsAuthenticated,),
            detail=False)
    def set_password(self, request):
        new_password = request.data.get('new_password')
        serilizer = SetPasswordSerializer(data=request.data,
                                          context={'request': request})
        serilizer.is_valid(raise_exception=True)
        request.user.password = make_password(new_password)
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST', 'DELETE'],
            permission_classes=(IsAuthenticated,),
            detail=True)
    def subscribe(self, request, pk):
        subscribe_to = self.get_object()
        if request.user == subscribe_to:
            return Response({'error': 'Вы не можете подписаться на себя'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = SubscribeSerializer(subscribe_to,
                                         context={'request': request})
        if request.method == 'POST':
            _, created = Subscribtion.objects.get_or_create(
                subscriber=request.user, subscribed_to=subscribe_to)
            if created:
                return Response(data=serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(
                {'error': 'Вы уже подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST)
        try:
            Subscribtion.objects.get(subscriber=request.user,
                                     subscribed_to_id=pk).delete()
        except Subscribtion.DoesNotExist:
            return Response({'error': 'Вы не подписаны'})
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

    @action(methods=['GET'],
            detail=False,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        current_user = User.objects.get(id=request.user.id)
        serializer = UserSerializer(current_user,
                                    context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(RetrieveListViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(RetrieveListViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('^name', 'name')


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
        serializer = ShortRecipeSerializer(recipe)
        if request.method == 'POST':
            _, created = FavoriteRecipe.objects.get_or_create(
                recipe=recipe, user=request.user)
            if created:
                return Response(
                    data=serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Рецепт уже в избранном'},
                                status=status.HTTP_400_BAD_REQUEST)
        try:
            FavoriteRecipe.objects.get(recipe=recipe,
                                       user=request.user).delete()
        except FavoriteRecipe.DoesNotExist:
            return Response({'error': 'Рецепт не был добавлен в избранное'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST', 'DELETE'],
            detail=True,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        recipe = self.get_object()
        serializer = ShortRecipeSerializer(recipe)
        if request.method == 'POST':
            _, created = ShoppingCart.objects.get_or_create(
                recipe=recipe, user=request.user)
            if created:
                return Response(
                    data=serializer.data, status=status.HTTP_201_CREATED)
            return Response({'error': 'Рецепт уже в списке покупок'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            ShoppingCart.objects.get(recipe=recipe, user=request.user).delete()
        except ShoppingCart.DoesNotExist:
            return Response({'error': 'Рецепта нет в списке покупок'},
                            status=status.HTTP_400_BAD_REQUEST)
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

        y = 800
        x = 50
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
