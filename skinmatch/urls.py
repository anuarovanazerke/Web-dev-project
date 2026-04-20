from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    AnalysisSessionListView,
    ProductListView,
    SkinProfileViewSet,
    analyze_face_and_match,
    app_options,
    check_ingredients,
    current_user,
    match_cosmetics,
    register_user,
)

router = DefaultRouter()
router.register(r"profile", SkinProfileViewSet, basename="skin-profile")

urlpatterns = [
    path("", include(router.urls)),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("analyses/", AnalysisSessionListView.as_view(), name="analysis-list"),
    path("options/", app_options, name="app-options"),
    path("auth/me/", current_user, name="current-user"),
    path("auth/register/", register_user, name="register-user"),
    path("match/", match_cosmetics, name="match-cosmetics"),
    path("analyze-face/", analyze_face_and_match, name="analyze-face"),
    path("check-ingredients/", check_ingredients, name="check-ingredients"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
