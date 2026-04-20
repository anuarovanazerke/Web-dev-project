from decimal import Decimal

from django.db import migrations


PRODUCTS = [
    {
        "name": "Hydra Comfort Cleanser",
        "brand": "CeraSkin",
        "category": "cleanser",
        "price": Decimal("14.90"),
        "recommended_for_skin": "dry",
        "concern_focus": "dehydration,sensitivity",
        "recommended_for_face_shape": "",
        "description": "Cream cleanser that keeps the barrier soft.",
        "is_budget_friendly": True,
    },
    {
        "name": "Pure Balance Gel",
        "brand": "CeraSkin",
        "category": "cleanser",
        "price": Decimal("12.50"),
        "recommended_for_skin": "oily",
        "concern_focus": "acne,dullness",
        "recommended_for_face_shape": "",
        "description": "Foaming cleanser for excess sebum.",
        "is_budget_friendly": True,
    },
    {
        "name": "Daily Calm Toner",
        "brand": "DermaMuse",
        "category": "toner",
        "price": Decimal("13.40"),
        "recommended_for_skin": "combo",
        "concern_focus": "sensitivity,dehydration",
        "recommended_for_face_shape": "",
        "description": "Alcohol-free toner for balancing combination skin.",
        "is_budget_friendly": True,
    },
    {
        "name": "Niacinamide Rescue Serum",
        "brand": "DermaMuse",
        "category": "serum",
        "price": Decimal("24.90"),
        "recommended_for_skin": "oily",
        "concern_focus": "acne,pigmentation",
        "recommended_for_face_shape": "",
        "description": "Serum for post-acne marks and visible pores.",
        "is_budget_friendly": False,
    },
    {
        "name": "Peptide Smooth Serum",
        "brand": "Lumiva",
        "category": "serum",
        "price": Decimal("28.90"),
        "recommended_for_skin": "normal",
        "concern_focus": "wrinkles,dullness",
        "recommended_for_face_shape": "",
        "description": "Peptide serum for early aging support.",
        "is_budget_friendly": False,
    },
    {
        "name": "Barrier Cream",
        "brand": "Lumiva",
        "category": "moisturizer",
        "price": Decimal("18.50"),
        "recommended_for_skin": "dry",
        "concern_focus": "dehydration,sensitivity",
        "recommended_for_face_shape": "",
        "description": "Rich cream for a compromised barrier.",
        "is_budget_friendly": True,
    },
    {
        "name": "Gel Balance Cream",
        "brand": "Lumiva",
        "category": "moisturizer",
        "price": Decimal("17.90"),
        "recommended_for_skin": "combo",
        "concern_focus": "acne,dehydration",
        "recommended_for_face_shape": "",
        "description": "Lightweight moisturizer that hydrates without heaviness.",
        "is_budget_friendly": True,
    },
    {
        "name": "Invisible Shield SPF 50",
        "brand": "Solaris",
        "category": "sunscreen",
        "price": Decimal("19.90"),
        "recommended_for_skin": "all",
        "concern_focus": "pigmentation,sensitivity",
        "recommended_for_face_shape": "",
        "description": "Universal daily sunscreen for every skin type.",
        "is_budget_friendly": True,
    },
    {
        "name": "Purifying Clay Mask",
        "brand": "Solaris",
        "category": "mask",
        "price": Decimal("16.50"),
        "recommended_for_skin": "oily",
        "concern_focus": "acne,dullness",
        "recommended_for_face_shape": "",
        "description": "Weekly clay mask for oil control.",
        "is_budget_friendly": True,
    },
    {
        "name": "Skin Tint Veil",
        "brand": "FaceForm",
        "category": "foundation",
        "price": Decimal("21.00"),
        "recommended_for_skin": "all",
        "concern_focus": "dullness",
        "recommended_for_face_shape": "oval,heart",
        "description": "Light base product that keeps the face natural.",
        "is_budget_friendly": True,
    },
    {
        "name": "Lift Concealer",
        "brand": "FaceForm",
        "category": "concealer",
        "price": Decimal("14.00"),
        "recommended_for_skin": "all",
        "concern_focus": "dullness",
        "recommended_for_face_shape": "oval,heart",
        "description": "Spot concealer with a natural finish.",
        "is_budget_friendly": True,
    },
    {
        "name": "Soft Sculpt Bronzer",
        "brand": "FaceForm",
        "category": "bronzer",
        "price": Decimal("18.00"),
        "recommended_for_skin": "all",
        "concern_focus": "dullness",
        "recommended_for_face_shape": "round,square,oblong",
        "description": "Bronzer for gentle visual contouring.",
        "is_budget_friendly": True,
    },
    {
        "name": "Cheek Harmony Blush",
        "brand": "FaceForm",
        "category": "blush",
        "price": Decimal("15.50"),
        "recommended_for_skin": "all",
        "concern_focus": "dullness",
        "recommended_for_face_shape": "round,square,heart,oblong",
        "description": "Soft blush that adds structure and freshness.",
        "is_budget_friendly": True,
    },
]

INGREDIENTS = [
    {
        "name": "Alcohol Denat",
        "is_dangerous": True,
        "description": "May be too drying for sensitive or dehydrated skin.",
    },
    {
        "name": "Fragrance",
        "is_dangerous": True,
        "description": "Can trigger irritation for reactive skin.",
    },
    {
        "name": "Niacinamide",
        "is_dangerous": False,
        "description": "Supports oil balance and post-acne marks.",
    },
    {
        "name": "Ceramide NP",
        "is_dangerous": False,
        "description": "Supports the skin barrier.",
    },
]


def seed_catalog(apps, schema_editor):
    Ingredient = apps.get_model("skinmatch", "Ingredient")
    Product = apps.get_model("skinmatch", "Product")

    for ingredient_data in INGREDIENTS:
        Ingredient.objects.update_or_create(
            name=ingredient_data["name"],
            defaults=ingredient_data,
        )

    for product_data in PRODUCTS:
        Product.objects.update_or_create(
            name=product_data["name"],
            brand=product_data["brand"],
            defaults=product_data,
        )


def unseed_catalog(apps, schema_editor):
    Product = apps.get_model("skinmatch", "Product")
    Ingredient = apps.get_model("skinmatch", "Ingredient")

    for product_data in PRODUCTS:
        Product.objects.filter(
            name=product_data["name"],
            brand=product_data["brand"],
        ).delete()

    for ingredient_data in INGREDIENTS:
        Ingredient.objects.filter(name=ingredient_data["name"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("skinmatch", "0002_alter_product_options_alter_recommendation_options_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_catalog, unseed_catalog),
    ]
