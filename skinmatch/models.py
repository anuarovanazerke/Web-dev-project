from django.contrib.auth.models import User
from django.db import models


class SkinProfile(models.Model):
    SKIN_TYPES = [
        ("dry", "Dry"),
        ("oily", "Oily"),
        ("combo", "Combination"),
        ("normal", "Normal"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="skin_profile",
    )
    skin_type = models.CharField(max_length=10, choices=SKIN_TYPES, verbose_name="Skin type")
    primary_concern = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Main problem",
    )
    budget_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Budget",
    )
    allergen_preferences = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Allergen preferences",
        help_text="Comma separated allergen identifiers to avoid.",
    )

    def __str__(self):
        return f"{self.user.username}: {self.skin_type}"


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Name")
    is_dangerous = models.BooleanField(default=False, verbose_name="Dangerous ingredient")
    is_common_allergen = models.BooleanField(default=False, verbose_name="Common allergen")
    description = models.TextField(blank=True, verbose_name="Description")
    allergy_note = models.TextField(blank=True, verbose_name="Allergy note")

    def __str__(self):
        return self.name


class Product(models.Model):
    SKIN_CHOICES = SkinProfile.SKIN_TYPES + [("all", "All skin types")]
    CATEGORY_CHOICES = [
        ("cleanser", "Cleanser"),
        ("toner", "Toner"),
        ("serum", "Serum"),
        ("moisturizer", "Moisturizer"),
        ("sunscreen", "Sunscreen"),
        ("mask", "Mask"),
        ("foundation", "Foundation"),
        ("concealer", "Concealer"),
        ("blush", "Blush"),
        ("bronzer", "Bronzer"),
    ]
    FACE_SHAPE_CHOICES = [
        ("oval", "Oval"),
        ("round", "Round"),
        ("square", "Square"),
        ("heart", "Heart"),
        ("oblong", "Oblong"),
        ("all", "All face shapes"),
    ]

    name = models.CharField(max_length=200, verbose_name="Product name")
    brand = models.CharField(max_length=100, verbose_name="Brand")
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="cleanser",
        verbose_name="Category",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    recommended_for_skin = models.CharField(
        max_length=10,
        choices=SKIN_CHOICES,
        default="all",
        verbose_name="Recommended skin type",
    )
    concern_focus = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Concerns",
        help_text="Comma separated concerns like acne,dehydration,pigmentation",
    )
    recommended_for_face_shape = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Face shapes",
        help_text="Comma separated face shapes like oval,round",
    )
    description = models.TextField(blank=True, verbose_name="Description")
    ingredient_summary = models.TextField(blank=True, verbose_name="Ingredient summary")
    image_url = models.URLField(blank=True, verbose_name="Image URL")
    is_budget_friendly = models.BooleanField(default=False)
    ingredients = models.ManyToManyField(Ingredient, blank=True, related_name="products")

    class Meta:
        ordering = ["price", "brand", "name"]

    def __str__(self):
        return f"{self.brand} - {self.name}"


class AnalysisSession(models.Model):
    FACE_SHAPE_CHOICES = Product.FACE_SHAPE_CHOICES[:-1]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analysis_sessions",
    )
    uploaded_image = models.ImageField(upload_to="analyses/")
    detected_skin_type = models.CharField(max_length=10, choices=SkinProfile.SKIN_TYPES)
    detected_face_shape = models.CharField(max_length=10, choices=FACE_SHAPE_CHOICES)
    detected_concern = models.CharField(max_length=100, blank=True)
    budget_limit = models.DecimalField(max_digits=10, decimal_places=2)
    total_selected_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    analysis_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Analysis #{self.pk} - {self.detected_skin_type}/{self.detected_face_shape}"


class Recommendation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recommendations",
        null=True,
        blank=True,
    )
    session = models.ForeignKey(
        AnalysisSession,
        on_delete=models.CASCADE,
        related_name="recommendations",
        null=True,
        blank=True,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="recommended_in",
    )
    reason = models.TextField(verbose_name="Reasons")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        target = self.user.username if self.user_id else f"session {self.session_id}"
        return f"Recommendation {self.product.name} for {target}"
