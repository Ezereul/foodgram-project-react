import csv
import logging

from django.core.management import BaseCommand

from recipes.models import Ingredient
from foodgram_api.settings import BASE_DIR


CSV_PATH = 'data/ingredients.csv'

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        if Ingredient.objects.exists():
            return

        file_path = BASE_DIR.parent.parent / CSV_PATH
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
            logger.info('Data loaded successfully')
