from django.core.management.base import BaseCommand

from skinmatch.catalog import SKINCARE_CATEGORIES
from skinmatch.models import Product


class Command(BaseCommand):
    help = "Delete non-skincare products from the local catalog."

    def handle(self, *args, **options):
        queryset = Product.objects.exclude(category__in=SKINCARE_CATEGORIES)
        deleted_count = queryset.count()
        queryset.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} non-skincare products."))
