from django.core.management.base import BaseCommand, CommandError

from skinmatch.catalog import SKINCARE_CATEGORIES
from skinmatch.curation import normalize_product_fields, should_keep_product
from skinmatch.importers.open_beauty_facts import (
    SEARCH_TERMS,
    fetch_open_beauty_facts,
    product_from_obf,
)
from skinmatch.models import Product


class Command(BaseCommand):
    help = "Import skincare-focused products from Open Beauty Facts into the local Product table."

    def add_arguments(self, parser):
        parser.add_argument("--limit-per-term", dest="limit_per_term", type=int, default=10)
        parser.add_argument(
            "--insecure",
            action="store_true",
            help="Disable SSL certificate verification for the remote request. Use only for local development.",
        )

    def handle(self, *args, **options):
        verify_ssl = not options["insecure"]
        limit = max(options["limit_per_term"], 1)
        created = 0
        updated = 0
        skipped = 0

        try:
            for term in SEARCH_TERMS:
                items = fetch_open_beauty_facts(term, page_size=limit, verify_ssl=verify_ssl)
                for item in items[:limit]:
                    mapped = product_from_obf(term, item)
                    if not mapped["name"] or mapped["category"] not in SKINCARE_CATEGORIES:
                        skipped += 1
                        continue

                    product, was_created = Product.objects.update_or_create(
                        brand=mapped["brand"],
                        name=mapped["name"],
                        defaults=mapped,
                    )
                    if not should_keep_product(product):
                        product.delete()
                        skipped += 1
                        continue
                    normalize_product_fields(product)
                    product.save()
                    if was_created:
                        created += 1
                    else:
                        updated += 1
        except Exception as exc:
            raise CommandError(f"Could not fetch skincare catalog: {exc}") from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Skincare import complete. Created: {created}, updated: {updated}, skipped: {skipped}."
            )
        )
