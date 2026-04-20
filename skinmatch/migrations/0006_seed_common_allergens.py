from django.db import migrations


ALLERGENS = [
    {
        "name": "Fragrance",
        "is_dangerous": True,
        "is_common_allergen": True,
        "description": "Can trigger irritation for reactive skin.",
        "allergy_note": "Often listed as parfum or perfume and may cause reactions in sensitive skin.",
    },
    {
        "name": "Alcohol Denat",
        "is_dangerous": True,
        "is_common_allergen": True,
        "description": "May be too drying for sensitive or dehydrated skin.",
        "allergy_note": "Can sting or worsen sensitivity in compromised skin barriers.",
    },
    {
        "name": "Lanolin",
        "is_dangerous": False,
        "is_common_allergen": True,
        "description": "Rich emollient, but can trigger reactions for some users.",
        "allergy_note": "Known contact allergen for a subset of users with wool alcohol sensitivity.",
    },
    {
        "name": "Limonene",
        "is_dangerous": False,
        "is_common_allergen": True,
        "description": "Fragrance component from essential oils.",
        "allergy_note": "Oxidized limonene can trigger allergic contact dermatitis.",
    },
    {
        "name": "Linalool",
        "is_dangerous": False,
        "is_common_allergen": True,
        "description": "Fragrance component from essential oils.",
        "allergy_note": "Often tolerated, but oxidized linalool can irritate sensitive skin.",
    },
]


def seed_allergens(apps, schema_editor):
    Ingredient = apps.get_model("skinmatch", "Ingredient")
    for data in ALLERGENS:
        Ingredient.objects.update_or_create(name=data["name"], defaults=data)


def unseed_allergens(apps, schema_editor):
    Ingredient = apps.get_model("skinmatch", "Ingredient")
    for data in ALLERGENS:
        Ingredient.objects.filter(name=data["name"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("skinmatch", "0005_product_media_allergens_and_profile_preferences"),
    ]

    operations = [
        migrations.RunPython(seed_allergens, unseed_allergens),
    ]
