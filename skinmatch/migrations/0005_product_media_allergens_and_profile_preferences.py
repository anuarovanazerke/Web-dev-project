from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("skinmatch", "0004_remove_seeded_decorative_products"),
    ]

    operations = [
        migrations.AddField(
            model_name="skinprofile",
            name="allergen_preferences",
            field=models.CharField(
                blank=True,
                help_text="Comma separated allergen identifiers to avoid.",
                max_length=255,
                verbose_name="Allergen preferences",
            ),
        ),
        migrations.AddField(
            model_name="ingredient",
            name="allergy_note",
            field=models.TextField(blank=True, verbose_name="Allergy note"),
        ),
        migrations.AddField(
            model_name="ingredient",
            name="is_common_allergen",
            field=models.BooleanField(default=False, verbose_name="Common allergen"),
        ),
        migrations.AddField(
            model_name="product",
            name="image_url",
            field=models.URLField(blank=True, verbose_name="Image URL"),
        ),
        migrations.AddField(
            model_name="product",
            name="ingredient_summary",
            field=models.TextField(blank=True, verbose_name="Ingredient summary"),
        ),
    ]
