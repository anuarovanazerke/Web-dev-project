from django.core.management.base import BaseCommand, CommandError

from skinmatch.importers.makeup_api import fetch_makeup_products, product_from_api
from skinmatch.models import Product


class Command(BaseCommand):
    help = "Import cosmetic products from the public Makeup API into the local Product table."

    def add_arguments(self, parser):
        parser.add_argument("--product-type", dest="product_type", default=None)
        parser.add_argument("--brand", dest="brand", default=None)
        parser.add_argument("--limit", dest="limit", type=int, default=50)
        parser.add_argument(
            "--insecure",
            action="store_true",
            help="Disable SSL certificate verification for the remote request. Use only for local development.",
        )

    def handle(self, *args, **options):
        try:
            products = fetch_makeup_products(
                product_type=options["product_type"],
                brand=options["brand"],
                verify_ssl=not options["insecure"],
            )
        except Exception as exc:
            raise CommandError(f"Could not fetch remote catalog: {exc}") from exc

        limit = max(options["limit"], 1)
        created = 0
        updated = 0
        skipped = 0

        for item in products[:limit]:
            mapped = product_from_api(item)
            if mapped["price"] <= 0:
                skipped += 1
                continue

            _, was_created = Product.objects.update_or_create(
                brand=mapped["brand"],
                name=mapped["name"],
                defaults=mapped,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete. Created: {created}, updated: {updated}, skipped: {skipped}."
            )
        )
