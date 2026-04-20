from django.core.management.base import BaseCommand

from skinmatch.curation import normalize_product_fields
from skinmatch.models import Product


class Command(BaseCommand):
    help = "Normalize product brand and product names for a cleaner storefront."

    def handle(self, *args, **options):
        updated = 0
        for product in Product.objects.all():
            original_brand = product.brand
            original_name = product.name
            normalize_product_fields(product)
            if product.brand != original_brand or product.name != original_name:
                product.save(update_fields=["brand", "name"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Catalog normalization complete. Updated: {updated}."))
