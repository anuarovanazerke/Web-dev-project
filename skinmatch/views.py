from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django.contrib.auth.models import User

from .allergens import ALLERGEN_CHOICES, ALLERGEN_KEYWORDS
from .catalog import SKINCARE_CATEGORIES
from .models import AnalysisSession, Ingredient, Product, Recommendation, SkinProfile
from .serializers import (
    AnalysisSessionSerializer,
    CONCERN_CHOICES,
    FaceAnalysisRequestSerializer,
    IngredientCheckSerializer,
    MatchRequestSerializer,
    ProductSerializer,
    RegisterSerializer,
    SkinProfileSerializer,
)
from .services import analyze_face_image, build_product_bundle, product_allergen_matches


class SkinProfileViewSet(viewsets.ModelViewSet):
    serializer_class = SkinProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SkinProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        profile = SkinProfile.objects.filter(user=request.user).first()
        payload = request.data.copy()
        allergens = payload.get("allergen_preferences", [])
        if isinstance(allergens, list):
            payload["allergen_preferences"] = ",".join(allergens)
        serializer = self.get_serializer(profile, data=payload, partial=bool(profile))
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        status_code = status.HTTP_200_OK if profile else status.HTTP_201_CREATED
        return Response(serializer.data, status=status_code)


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = list(
            Product.objects.filter(category__in=SKINCARE_CATEGORIES)
            .prefetch_related("ingredients")
            .order_by("-is_budget_friendly", "price", "brand", "name")
        )
        category = self.request.query_params.get("category")
        skin_type = self.request.query_params.get("skin_type")
        concern = self.request.query_params.get("concern")
        allergen_param = self.request.query_params.get("allergens", "")
        allergens = [item.strip() for item in allergen_param.split(",") if item.strip()]

        if category:
            queryset = [item for item in queryset if item.category == category]
        if skin_type:
            queryset = [
                item for item in queryset if item.recommended_for_skin in [skin_type, "all"]
            ]
        if concern:
            queryset = [
                item for item in queryset if concern.lower() in (item.concern_focus or "").lower()
            ]
        if allergens:
            queryset = [
                item for item in queryset if not product_allergen_matches(item, allergens)
            ]
        return queryset


class AnalysisSessionListView(generics.ListAPIView):
    serializer_class = AnalysisSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AnalysisSession.objects.filter(user=self.request.user).prefetch_related(
            "recommendations__product__ingredients"
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def app_options(request):
    return Response(
        {
            "skin_types": [
                {"value": value, "label": label} for value, label in SkinProfile.SKIN_TYPES
            ],
            "face_shapes": [
                {"value": value, "label": label}
                for value, label in Product.FACE_SHAPE_CHOICES[:-1]
            ],
            "concerns": [
                {"value": value, "label": label} for value, label in CONCERN_CHOICES if value
            ],
            "categories": [
                {"value": value, "label": label}
                for value, label in Product.CATEGORY_CHOICES
                if value in SKINCARE_CATEGORIES
            ],
            "allergens": [
                {"value": value, "label": label} for value, label in ALLERGEN_CHOICES
            ],
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    profile = SkinProfile.objects.filter(user=request.user).first()
    return Response(
        {
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "profile": SkinProfileSerializer(profile).data if profile else None,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    if User.objects.filter(username=data["username"]).exists():
        return Response({"username": ["This username is already taken."]}, status=400)

    user = User.objects.create_user(
        username=data["username"],
        password=data["password"],
        email=data.get("email", ""),
    )

    if data.get("skin_type") or data.get("primary_concern") or data.get("budget_limit") is not None:
        SkinProfile.objects.create(
            user=user,
            skin_type=data.get("skin_type") or "normal",
            primary_concern=data.get("primary_concern", ""),
            budget_limit=data.get("budget_limit"),
            allergen_preferences=",".join(data.get("allergen_preferences", [])),
        )

    return Response(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def match_cosmetics(request):
    serializer = MatchRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    bundle = build_product_bundle(
        skin_type=data["skin_type"],
        concern=data.get("concern", ""),
        face_shape=data.get("face_shape", ""),
        budget=data["budget"],
        allergens=data.get("allergens", []),
    )

    payload = []
    for item in bundle["recommendations"]:
        serialized = ProductSerializer(item["product"]).data
        serialized["match_reason"] = item["reason"]
        serialized["match_score"] = item["score"]
        payload.append(serialized)

    return Response(
        {
            "count": len(payload),
            "total_price": bundle["total_price"],
            "remaining_budget": bundle["remaining_budget"],
            "selected_categories": bundle["selected_categories"],
            "ingredient_hints": bundle["ingredient_hints"],
            "allergen_filters": bundle["allergen_filters"],
            "recommendations": payload,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def analyze_face_and_match(request):
    serializer = FaceAnalysisRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    analysis = analyze_face_image(data["image"], data.get("concern", ""))
    bundle = build_product_bundle(
        skin_type=analysis["skin_type"],
        concern=analysis["concern"],
        face_shape=analysis["face_shape"],
        budget=data["budget"],
        allergens=data.get("allergens", []),
    )

    session = AnalysisSession.objects.create(
        user=request.user if request.user.is_authenticated else None,
        uploaded_image=data["image"],
        detected_skin_type=analysis["skin_type"],
        detected_face_shape=analysis["face_shape"],
        detected_concern=analysis["concern"],
        budget_limit=data["budget"],
        total_selected_price=bundle["total_price"],
        analysis_notes=analysis["notes"],
    )

    recommendation_payload = []
    for item in bundle["recommendations"]:
        recommendation = Recommendation.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session=session,
            product=item["product"],
            reason=item["reason"],
        )
        serialized = ProductSerializer(item["product"]).data
        serialized["match_reason"] = recommendation.reason
        serialized["match_score"] = item["score"]
        recommendation_payload.append(serialized)

    session_data = AnalysisSessionSerializer(session).data
    session_data["recommendations"] = recommendation_payload

    return Response(
        {
            "analysis": {
                "provider": analysis.get("provider", "heuristic"),
                "skin_type": analysis["skin_type"],
                "face_shape": analysis["face_shape"],
                "concern": analysis["concern"],
                "notes": analysis["notes"],
                "metrics": analysis["metrics"],
                "ingredient_hints": analysis["ingredient_hints"],
            },
            "budget": {
                "limit": data["budget"],
                "selected_total": bundle["total_price"],
                "remaining": bundle["remaining_budget"],
            },
            "allergen_filters": bundle["allergen_filters"],
            "session": session_data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def check_ingredients(request):
    serializer = IngredientCheckSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    text = serializer.validated_data["ingredients_text"].lower()
    dangerous_found = Ingredient.objects.filter(is_dangerous=True)
    allergen_targets = serializer.validated_data.get("allergens", [])
    found_list = []
    allergen_list = []

    for ingredient in dangerous_found:
        if ingredient.name.lower() in text:
            found_list.append(
                {
                    "name": ingredient.name,
                    "danger": ingredient.description,
                }
            )

    for value, label in ALLERGEN_CHOICES:
        if value not in allergen_targets:
            continue
        matches = [
            keyword for keyword in ALLERGEN_KEYWORDS.get(value, []) if keyword in text
        ]
        if matches:
            allergen_list.append(
                {
                    "allergen": value,
                    "label": label,
                    "matched_keywords": sorted(set(matches)),
                }
            )

    return Response(
        {
            "is_safe": len(found_list) == 0 and len(allergen_list) == 0,
            "dangerous_ingredients": found_list,
            "allergen_alerts": allergen_list,
        },
        status=status.HTTP_200_OK,
    )
