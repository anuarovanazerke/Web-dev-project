from django.db import migrations


DECORATIVE_NAMES = [
    ("FaceForm", "Skin Tint Veil"),
    ("FaceForm", "Lift Concealer"),
    ("FaceForm", "Soft Sculpt Bronzer"),
    ("FaceForm", "Cheek Harmony Blush"),
]


def remove_decorative_products(apps, schema_editor):
    Product = apps.get_model("skinmatch", "Product")
    for brand, name in DECORATIVE_NAMES:
        Product.objects.filter(brand=brand, name=name).delete()


def restore_decorative_products(apps, schema_editor):
    Product = apps.get_model("skinmatch", "Product")
    Product.objects.update_or_create(
        brand="FaceForm",
        name="Skin Tint Veil",
        defaults={
            "category": "foundation",
            "price": "21.00",
            "recommended_for_skin": "all",
            "concern_focus": "dullness",
            "recommended_for_face_shape": "oval,heart",
            "description": "Light base product that keeps the face natural.",
            "is_budget_friendly": True,
        },
    )
    Product.objects.update_or_create(
        brand="FaceForm",
        name="Lift Concealer",
        defaults={
            "category": "concealer",
            "price": "14.00",
            "recommended_for_skin": "all",
            "concern_focus": "dullness",
            "recommended_for_face_shape": "oval,heart",
            "description": "Spot concealer with a natural finish.",
            "is_budget_friendly": True,
        },
    )
    Product.objects.update_or_create(
        brand="FaceForm",
        name="Soft Sculpt Bronzer",
        defaults={
            "category": "bronzer",
            "price": "18.00",
            "recommended_for_skin": "all",
            "concern_focus": "dullness",
            "recommended_for_face_shape": "round,square,oblong",
            "description": "Bronzer for gentle visual contouring.",
            "is_budget_friendly": True,
        },
    )
    Product.objects.update_or_create(
        brand="FaceForm",
        name="Cheek Harmony Blush",
        defaults={
            "category": "blush",
            "price": "15.50",
            "recommended_for_skin": "all",
            "concern_focus": "dullness",
            "recommended_for_face_shape": "round,square,heart,oblong",
            "description": "Soft blush that adds structure and freshness.",
            "is_budget_friendly": True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("skinmatch", "0003_seed_catalog"),
    ]

    operations = [
        migrations.RunPython(remove_decorative_products, restore_decorative_products),
    ]
