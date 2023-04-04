from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        blank=False,
        unique=True,
        validators=[UnicodeUsernameValidator()],
        verbose_name='Имя пользователя'
    )
    first_name = models.CharField(max_length=150, verbose_name='Имя')
    last_name = models.CharField(max_length=150, verbose_name='Фамилия')
    email = models.EmailField(blank=False, unique=True, verbose_name='Email')
    groups = models.ManyToManyField(Group, verbose_name='groups', blank=True,
                                    related_name='users_user_groups')
    user_permissions = models.ManyToManyField(
        Permission, verbose_name='user permissions', blank=True,
        related_name='users_user_permissions')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username



class Subscribtion(models.Model):
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик')
    subscribed_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribing')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'subscribed_to'],
                name='unique_subscribe')
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
