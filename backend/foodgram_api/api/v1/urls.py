from django.urls import include, path
from djoser.views import UserViewSet
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                    SubscriptionViewSet)

v1_router = DefaultRouter()

v1_router.register('tags', TagViewSet)
v1_router.register('ingredients', IngredientViewSet)
v1_router.register('recipes', RecipeViewSet)


urlpatterns = [
    path('', include(v1_router.urls)),
    path('users/', UserViewSet.as_view(
        {'get': 'list', 'post': 'create'}), name='user-list-create'),
    path('users/<int:id>/', UserViewSet.as_view(
        {'get': 'retrieve'}), name='user-detail'),
    path('users/me/', UserViewSet.as_view(
        {'get': 'me'}), name='user-me'),
    path('users/set_password/', UserViewSet.as_view(
        {'post': 'set_password'}), name='user-set-password'),
    path('users/subscriptions/', SubscriptionViewSet.as_view(
        {'get': 'subscriptions'}), name='user-subscriptions'),
    path('users/<int:pk>/subscribe/', SubscriptionViewSet.as_view(
        {'post': 'subscribe', 'delete': 'subscribe'}), name='user-subscribe'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken'))
]
