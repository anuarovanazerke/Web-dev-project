from django.contrib import admin

from .models import AnalysisSession, Ingredient, Product, Recommendation, SkinProfile


@admin.register(SkinProfile)
class SkinProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "skin_type", "primary_concern", "budget_limit")


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "is_dangerous")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "brand",
        "name",
        "category",
        "recommended_for_skin",
        "price",
        "is_budget_friendly",
    )
    list_filter = ("category", "recommended_for_skin", "is_budget_friendly")
    search_fields = ("brand", "name", "concern_focus", "recommended_for_face_shape")


@admin.register(AnalysisSession)
class AnalysisSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "detected_skin_type",
        "detected_face_shape",
        "detected_concern",
        "budget_limit",
        "total_selected_price",
        "created_at",
    )
    list_filter = ("detected_skin_type", "detected_face_shape", "created_at")


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "session", "created_at")
    search_fields = ("product__name", "reason")
