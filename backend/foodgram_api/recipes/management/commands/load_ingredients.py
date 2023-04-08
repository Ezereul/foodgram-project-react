import csv
import logging

from django.conf import settings
from django.core.management import BaseCommand
from recipes.models import Ingredient, Tag

logger = logging.getLogger(__name__)


BASE_DIR = settings.BASE_DIR


def load_ingredients():
    if Ingredient.objects.exists():
        return

    file_path = BASE_DIR / 'data/ingredients.csv'
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        data = csv.reader(file, delimiter=',')
        ingredients = []
        for row in data:
            ingredient = Ingredient(
                name=row[0],
                measurement_unit=row[1]
            )
            ingredients.append(ingredient)
        if ingredients:
            Ingredient.objects.bulk_create(ingredients)


def load_tags():
    if Tag.objects.exists():
        return

    file_path = BASE_DIR / 'tags.csv'
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        data = csv.reader(file, delimiter=',')
        tags = []
        for row in data:
            tag = Tag(
                name=row[0],
                color=row[1],
                slug=row[2]
            )
            tags.append(tag)
        if tags:
            Tag.objects.bulk_create(tags)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            load_ingredients()
            load_tags()
        except Exception as e:
            logger.error(e)
            return
        logger.info('Data loaded successfully')
