import csv
import os

from django.core.management.base import BaseCommand
from reviews.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from CSV file'

    def handle(self, *args, **kwargs):
        file_path = os.path.join('app', 'data', 'ingredients.csv')
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ingredient, created = Ingredient.objects.get_or_create(
                    name=row['name'],
                    measurement_unit=row['measurement_unit']
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'Ingredient "{ingredient.name}" added.'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'Ingredient "{ingredient.name}" already exists.'
                    ))
