from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Subscribtion

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email')
    list_filter = ('email', 'username')
    search_fields = ('email', 'username')


@admin.register(Subscribtion)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'subscribed_to')
    search_fields = ('subscriber__username', 'subscribed_to__username')
