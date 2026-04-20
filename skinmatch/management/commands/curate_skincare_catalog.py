from django.core.management.base import BaseCommand

from skinmatch.curation import should_keep_product
from skinmatch.models import Product


class Command(BaseCommand):
    help = "Remove low-quality or obviously irrelevant skincare products from the catalog."

    def handle(self, *args, **options):
        deleted = 0
        for product in Product.objects.all():
            if not should_keep_product(product):
                product.delete()
                deleted += 1

        self.stdout.write(self.style.SUCCESS(f"Catalog curation complete. Deleted: {deleted}."))
