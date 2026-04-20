from rest_framework import serializers

from .allergens import ALLERGEN_CHOICES
from .models import AnalysisSession, Ingredient, Product, Recommendation, SkinProfile
from .presentation import placeholder_image_url


CONCERN_CHOICES = [
    ("", "No specific concern"),
    ("acne", "Acne"),
    ("rosacea", "Rosacea"),
    ("wrinkles", "Wrinkles"),
    ("pigmentation", "Pigmentation"),
    ("dehydration", "Dehydration"),
    ("sensitivity", "Sensitivity"),
    ("dullness", "Dullness"),
    ("pores", "Visible pores"),
    ("dark_circles", "Dark circles"),
]


class SkinProfileSerializer(serializers.ModelSerializer):
    allergen_tags = serializers.SerializerMethodField()

    class Meta:
        model = SkinProfile
        fields = [
            "id",
            "user",
            "skin_type",
            "primary_concern",
            "budget_limit",
            "allergen_preferences",
            "allergen_tags",
        ]
        read_only_fields = ["user"]

    def get_allergen_tags(self, obj):
        return [item.strip() for item in (obj.allergen_preferences or "").split(",") if item.strip()]


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "is_dangerous", "is_common_allergen", "description", "allergy_note"]


class ProductSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True, read_only=True)
    concern_tags = serializers.SerializerMethodField()
    face_shape_tags = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "brand",
            "category",
            "price",
            "recommended_for_skin",
            "concern_focus",
            "recommended_for_face_shape",
            "concern_tags",
            "face_shape_tags",
            "description",
            "ingredient_summary",
            "image_url",
            "is_budget_friendly",
            "ingredients",
        ]

    def get_concern_tags(self, obj):
        return [item.strip() for item in obj.concern_focus.split(",") if item.strip()]

    def get_face_shape_tags(self, obj):
        return [item.strip() for item in obj.recommended_for_face_shape.split(",") if item.strip()]

    def get_image_url(self, obj):
        return obj.image_url or placeholder_image_url(obj.category, obj.brand, obj.name)


class RecommendationSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Recommendation
        fields = ["id", "product", "reason", "created_at"]


class AnalysisSessionSerializer(serializers.ModelSerializer):
    recommendations = RecommendationSerializer(many=True, read_only=True)

    class Meta:
        model = AnalysisSession
        fields = [
            "id",
            "uploaded_image",
            "detected_skin_type",
            "detected_face_shape",
            "detected_concern",
            "budget_limit",
            "total_selected_price",
            "analysis_notes",
            "created_at",
            "recommendations",
        ]
        read_only_fields = [
            "detected_skin_type",
            "detected_face_shape",
            "detected_concern",
            "total_selected_price",
            "analysis_notes",
            "created_at",
            "recommendations",
        ]


class MatchRequestSerializer(serializers.Serializer):
    skin_type = serializers.ChoiceField(choices=[choice[0] for choice in SkinProfile.SKIN_TYPES])
    face_shape = serializers.ChoiceField(
        choices=[choice[0] for choice in Product.FACE_SHAPE_CHOICES[:-1]],
        required=False,
        allow_blank=True,
    )
    budget = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    concern = serializers.ChoiceField(choices=CONCERN_CHOICES, required=False, allow_blank=True)
    allergens = serializers.ListField(
        child=serializers.ChoiceField(choices=ALLERGEN_CHOICES),
        required=False,
        allow_empty=True,
    )


class FaceAnalysisRequestSerializer(serializers.Serializer):
    image = serializers.ImageField()
    budget = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    concern = serializers.ChoiceField(choices=CONCERN_CHOICES, required=False, allow_blank=True)
    allergens = serializers.ListField(
        child=serializers.ChoiceField(choices=ALLERGEN_CHOICES),
        required=False,
        allow_empty=True,
    )


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    email = serializers.EmailField(required=False, allow_blank=True)
    skin_type = serializers.ChoiceField(
        choices=[choice[0] for choice in SkinProfile.SKIN_TYPES],
        required=False,
        allow_blank=True,
    )
    primary_concern = serializers.ChoiceField(choices=CONCERN_CHOICES, required=False, allow_blank=True)
    allergen_preferences = serializers.ListField(
        child=serializers.ChoiceField(choices=ALLERGEN_CHOICES),
        required=False,
        allow_empty=True,
    )
    budget_limit = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,
        allow_null=True,
    )


class IngredientCheckSerializer(serializers.Serializer):
    ingredients_text = serializers.CharField(
        style={"base_template": "textarea.html"},
        help_text="Enter ingredients list, for example: Aqua, Glycerin, Alcohol.",
    )
    allergens = serializers.ListField(
        child=serializers.ChoiceField(choices=ALLERGEN_CHOICES),
        required=False,
        allow_empty=True,
    )
