from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from PIL import Image

from .catalog import SKINCARE_CATEGORIES
from .curation import normalize_product_fields, should_keep_product
from .importers.makeup_api import infer_concerns, map_product_type, product_from_api
from .importers.open_beauty_facts import map_category, product_from_obf
from .models import Product
from .services import build_product_bundle


def generate_test_image(name="face.png", color=(210, 180, 170)):
    buffer = BytesIO()
    image = Image.new("RGB", (180, 240), color=color)
    image.save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class BundleSelectionTests(TestCase):
    def setUp(self):
        Product.objects.create(
            name="Soft Clean Gel",
            brand="SkinM",
            category="cleanser",
            price=Decimal("15.00"),
            recommended_for_skin="combo",
            concern_focus="acne",
            description="Daily cleanser",
            is_budget_friendly=True,
        )
        Product.objects.create(
            name="Balance Cream",
            brand="SkinM",
            category="moisturizer",
            price=Decimal("20.00"),
            recommended_for_skin="combo",
            concern_focus="acne,dehydration",
            description="Gel cream",
            is_budget_friendly=True,
        )
        Product.objects.create(
            name="Light SPF",
            brand="SkinM",
            category="sunscreen",
            price=Decimal("18.00"),
            recommended_for_skin="all",
            concern_focus="pigmentation",
            description="SPF 50",
            is_budget_friendly=True,
        )
        Product.objects.create(
            name="Clear Serum",
            brand="SkinM",
            category="serum",
            price=Decimal("24.00"),
            recommended_for_skin="combo",
            concern_focus="acne",
            description="Niacinamide serum",
            is_budget_friendly=False,
        )

    def test_bundle_does_not_exceed_budget(self):
        bundle = build_product_bundle("combo", "acne", "oval", Decimal("60.00"))

        self.assertLessEqual(bundle["total_price"], Decimal("60.00"))
        self.assertGreaterEqual(len(bundle["recommendations"]), 3)
        self.assertIn("cleanser", bundle["selected_categories"])
        self.assertIn("moisturizer", bundle["selected_categories"])
        self.assertIn("sunscreen", bundle["selected_categories"])


class FaceAnalysisApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        Product.objects.create(
            name="Daily Cleanser",
            brand="SkinM",
            category="cleanser",
            price=Decimal("12.00"),
            recommended_for_skin="oily",
            concern_focus="acne",
            description="Foaming cleanser",
            is_budget_friendly=True,
        )
        Product.objects.create(
            name="Fresh Cream",
            brand="SkinM",
            category="moisturizer",
            price=Decimal("16.00"),
            recommended_for_skin="oily",
            concern_focus="acne",
            description="Light cream",
            is_budget_friendly=True,
        )
        Product.objects.create(
            name="Urban SPF",
            brand="SkinM",
            category="sunscreen",
            price=Decimal("19.00"),
            recommended_for_skin="all",
            concern_focus="pigmentation",
            description="Invisible sunscreen",
            is_budget_friendly=True,
        )

    def test_analyze_face_endpoint_returns_recommendations(self):
        response = self.client.post(
            "/api/analyze-face/",
            {
                "image": generate_test_image(),
                "budget": "50.00",
                "concern": "acne",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("analysis", response.data)
        self.assertIn("session", response.data)
        self.assertGreaterEqual(len(response.data["session"]["recommendations"]), 1)


class MakeupImporterTests(TestCase):
    def test_maps_product_type_to_supported_category(self):
        self.assertEqual(map_product_type("foundation"), "foundation")
        self.assertEqual(map_product_type("lipstick"), "foundation")
        self.assertEqual(map_product_type("cleanser"), "cleanser")

    def test_infers_concerns_from_tags_and_description(self):
        concerns = infer_concerns(
            {
                "tag_list": ["Oil Free", "Vegan"],
                "name": "Glow Serum",
                "description": "Brightening vitamin C treatment for dark spot care",
            }
        )
        self.assertIn("acne", concerns)
        self.assertIn("pigmentation", concerns)

    def test_maps_api_product_to_local_product_shape(self):
        product = product_from_api(
            {
                "brand": "BrandX",
                "name": "Hydrating Foundation",
                "product_type": "foundation",
                "price": "12.5",
                "description": "Hydrating glow formula for dry skin",
                "tag_list": [],
            }
        )
        self.assertEqual(product["brand"], "BrandX")
        self.assertEqual(product["category"], "foundation")
        self.assertEqual(product["recommended_for_skin"], "dry")


class SkincareCatalogTests(TestCase):
    def test_bundle_contains_only_skincare_categories(self):
        bundle = build_product_bundle("combo", "acne", "oval", Decimal("60.00"))
        for category in bundle["selected_categories"]:
            self.assertIn(category, SKINCARE_CATEGORIES)

    def test_open_beauty_facts_mapping_stays_in_skincare_categories(self):
        mapped = product_from_obf(
            "face mask",
            {
                "product_name": "Hydrating Face Mask",
                "generic_name": "Face mask with hyaluronic acid",
                "ingredients_text_en": "hyaluronic acid, glycerin",
                "brands": "CareLab",
            },
        )
        self.assertEqual(map_category("face mask", {"product_name": "Hydrating Face Mask"}), "mask")
        self.assertIn(mapped["category"], SKINCARE_CATEGORIES)

    def test_curation_rejects_unknown_or_low_quality_products(self):
        bad = Product(
            brand="Unknown Brand",
            name="Unnamed product",
            category="cleanser",
            price=Decimal("19.90"),
            recommended_for_skin="all",
        )
        good = Product(
            brand="CeraVe",
            name="Hydrating Cleanser",
            category="cleanser",
            price=Decimal("19.90"),
            recommended_for_skin="dry",
        )
        self.assertFalse(should_keep_product(bad))
        self.assertTrue(should_keep_product(good))

    def test_normalization_polishes_brand_and_name(self):
        product = Product(
            brand="la roche - posay",
            name="retinol serum b3",
            category="serum",
            price=Decimal("19.90"),
            recommended_for_skin="all",
        )
        normalize_product_fields(product)
        self.assertEqual(product.brand, "La Roche-Posay")
        self.assertEqual(product.name, "Retinol Serum B3")
