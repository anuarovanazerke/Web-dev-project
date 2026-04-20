from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from PIL import Image, ImageStat

from .allergens import ALLERGEN_KEYWORDS
from .catalog import SKINCARE_CATEGORIES
from .models import Product


ESSENTIAL_CATEGORIES = ["cleanser", "moisturizer", "sunscreen"]
CONCERN_CATEGORY_MAP = {
    "acne": ["serum", "mask"],
    "rosacea": ["toner", "moisturizer"],
    "wrinkles": ["serum", "moisturizer"],
    "pigmentation": ["serum", "toner"],
    "dehydration": ["serum", "mask"],
    "sensitivity": ["toner", "mask"],
    "dullness": ["serum", "mask"],
    "pores": ["serum", "mask"],
    "dark_circles": ["serum", "mask"],
}
INGREDIENT_RECOMMENDATIONS = {
    "acne": ["niacinamide", "salicylic acid"],
    "rosacea": ["azelaic acid", "ceramides"],
    "wrinkles": ["retinol", "peptides"],
    "pigmentation": ["vitamin c", "niacinamide"],
    "dehydration": ["hyaluronic acid", "ceramides"],
    "sensitivity": ["centella", "ceramides"],
    "dullness": ["vitamin c", "pha"],
    "pores": ["niacinamide", "bha"],
    "dark_circles": ["caffeine", "peptides"],
}


def normalize_concern(value):
    text = (value or "").strip().lower()
    if not text:
        return ""

    concern_aliases = {
        "pimples": "acne",
        "breakouts": "acne",
        "acne": "acne",
        "rosacea": "rosacea",
        "wrinkle": "wrinkles",
        "wrinkles": "wrinkles",
        "aging": "wrinkles",
        "dehydrated": "dehydration",
        "dehydration": "dehydration",
        "dryness": "dehydration",
        "spots": "pigmentation",
        "pigmentation": "pigmentation",
        "redness": "rosacea",
        "sensitive": "sensitivity",
        "sensitivity": "sensitivity",
        "dull": "dullness",
        "dullness": "dullness",
        "pores": "pores",
        "dark circles": "dark_circles",
        "dark_circles": "dark_circles",
    }
    return concern_aliases.get(text, text)


def _csv_contains(csv_text, needle):
    if not csv_text or not needle:
        return False
    values = {item.strip().lower() for item in csv_text.split(",") if item.strip()}
    return "all" in values or needle.lower() in values


def product_allergen_matches(product, allergens):
    if not allergens:
        return []

    text_parts = [product.ingredient_summary or "", product.description or ""]
    if hasattr(product, "ingredients"):
        text_parts.extend(ingredient.name for ingredient in product.ingredients.all())
    haystack = " ".join(text_parts).lower()

    matches = []
    for allergen in allergens:
        keywords = ALLERGEN_KEYWORDS.get(allergen, [])
        if any(keyword in haystack for keyword in keywords):
            matches.append(allergen)
    return matches


def _analyze_face_image_heuristic(uploaded_file, concern_hint=""):
    image = Image.open(uploaded_file).convert("RGB")
    image.thumbnail((256, 256))

    width, height = image.size
    stat = ImageStat.Stat(image)
    mean_r, mean_g, mean_b = stat.mean
    std_r, std_g, std_b = stat.stddev

    brightness = (mean_r + mean_g + mean_b) / 3
    contrast = (std_r + std_g + std_b) / 3
    warmth_ratio = mean_r / max(mean_b, 1)
    aspect_ratio = width / max(height, 1)

    if brightness >= 165 and contrast >= 52:
        skin_type = "oily"
    elif brightness <= 105 or contrast <= 32:
        skin_type = "dry"
    elif 115 <= brightness <= 165 and contrast >= 40:
        skin_type = "combo"
    else:
        skin_type = "normal"

    if aspect_ratio < 0.70:
        face_shape = "oblong"
    elif aspect_ratio < 0.78:
        face_shape = "oval"
    elif aspect_ratio < 0.88:
        face_shape = "round"
    elif warmth_ratio > 1.18 and contrast < 42:
        face_shape = "heart"
    else:
        face_shape = "square"

    declared_concern = normalize_concern(concern_hint)
    if declared_concern:
        concern = declared_concern
    elif contrast >= 60:
        concern = "acne"
    elif brightness <= 110:
        concern = "dehydration"
    elif warmth_ratio >= 1.20:
        concern = "pigmentation"
    else:
        concern = "dullness"

    ingredient_hints = INGREDIENT_RECOMMENDATIONS.get(concern, [])
    notes = (
        "Lightweight visual analysis used. "
        f"brightness={brightness:.1f}, contrast={contrast:.1f}, "
        f"warmth_ratio={warmth_ratio:.2f}, aspect_ratio={aspect_ratio:.2f}. "
        f"Suggested actives: {', '.join(ingredient_hints) if ingredient_hints else 'basic barrier-supporting care'}."
    )

    uploaded_file.seek(0)
    return {
        "provider": "heuristic",
        "skin_type": skin_type,
        "face_shape": face_shape,
        "concern": concern,
        "notes": notes,
        "metrics": {
            "brightness": round(brightness, 2),
            "contrast": round(contrast, 2),
            "warmth_ratio": round(warmth_ratio, 2),
            "aspect_ratio": round(aspect_ratio, 2),
        },
        "ingredient_hints": ingredient_hints,
    }


def analyze_face_image(uploaded_file, concern_hint=""):
    provider = getattr(settings, "FACE_ANALYSIS_PROVIDER", "openai").lower().strip()
    if provider == "openai":
        from .ai_analysis import FaceAnalysisProviderError, analyze_face_with_ai

        try:
            return analyze_face_with_ai(uploaded_file, concern_hint=concern_hint)
        except FaceAnalysisProviderError as e:
            print("AI ERROR:", e)
            uploaded_file.seek(0)

    return _analyze_face_image_heuristic(uploaded_file, concern_hint=concern_hint)


def _product_score(product, skin_type, concern, face_shape):
    score = 0
    if product.recommended_for_skin in {skin_type, "all"}:
        score += 4 if product.recommended_for_skin == skin_type else 2
    if concern and _csv_contains(product.concern_focus, concern):
        score += 3
    if face_shape and _csv_contains(product.recommended_for_face_shape, face_shape):
        score += 2
    if product.is_budget_friendly:
        score += 1
    return score


def _candidate_queryset(skin_type, concern, face_shape, allergens=None):
    products = Product.objects.filter(category__in=SKINCARE_CATEGORIES).prefetch_related("ingredients")
    candidates = []
    for product in products:
        if product.recommended_for_skin not in {skin_type, "all"}:
            continue
        allergen_matches = product_allergen_matches(product, allergens or [])
        if allergen_matches:
            continue
        score = _product_score(product, skin_type, concern, face_shape)
        if score > 0:
            candidates.append((product, score))
    return candidates


def _pick_for_categories(scored_products, ordered_categories, budget, reserve_remaining=False):
    by_category = defaultdict(list)
    for product, score in scored_products:
        by_category[product.category].append((product, score))

    for category in by_category:
        by_category[category].sort(key=lambda item: (-item[1], item[0].price))

    selected = []
    used_categories = set()
    total = Decimal("0")

    for category in ordered_categories:
        if category in used_categories:
            continue
        candidates = by_category.get(category, [])
        if not candidates:
            continue

        reserved_minimum = Decimal("0")
        if reserve_remaining:
            remaining_categories = [
                item for item in ordered_categories if item not in used_categories and item != category
            ]
            for remaining in remaining_categories:
                remaining_candidates = by_category.get(remaining, [])
                if remaining_candidates:
                    reserved_minimum += min(candidate[0].price for candidate in remaining_candidates)

        for product, score in candidates:
            new_total = total + product.price
            if new_total + reserved_minimum <= budget:
                selected.append((product, score))
                used_categories.add(category)
                total = new_total
                break

    return selected, total


def build_product_bundle(skin_type, concern, face_shape, budget, allergens=None):
    budget = Decimal(str(budget))
    concern = normalize_concern(concern)
    allergens = allergens or []
    scored_products = _candidate_queryset(skin_type, concern, face_shape, allergens=allergens)

    optional_categories = []
    optional_categories.extend(CONCERN_CATEGORY_MAP.get(concern, []))
    seen = set()
    ordered_optional = []
    for category in optional_categories:
        if category not in seen and category not in ESSENTIAL_CATEGORIES:
            ordered_optional.append(category)
            seen.add(category)

    selected, total = _pick_for_categories(
        scored_products,
        ESSENTIAL_CATEGORIES,
        budget,
        reserve_remaining=True,
    )

    optional_selected, optional_total = _pick_for_categories(
        [
            item
            for item in scored_products
            if item[0].category not in {product.category for product, _score in selected}
        ],
        ordered_optional,
        budget - total,
        reserve_remaining=False,
    )
    selected.extend(optional_selected)
    total += optional_total

    if not selected:
        fallback = sorted(scored_products, key=lambda item: (item[0].price, -item[1]))
        used_categories = set()
        for product, score in fallback:
            if product.category in used_categories:
                continue
            if total + product.price > budget:
                continue
            selected.append((product, score))
            used_categories.add(product.category)
            total += product.price

    recommendations = []
    ingredient_hints = INGREDIENT_RECOMMENDATIONS.get(concern, [])
    for product, score in selected:
        reasons = [f"matches skin type: {skin_type}"]
        if concern and _csv_contains(product.concern_focus, concern):
            reasons.append(f"targets concern: {concern}")
        if face_shape and _csv_contains(product.recommended_for_face_shape, face_shape):
            reasons.append(f"suits face shape: {face_shape}")
        if product.is_budget_friendly:
            reasons.append("good value for budget")
        if ingredient_hints:
            reasons.append(f"helpful actives: {', '.join(ingredient_hints)}")

        recommendations.append(
            {
                "product": product,
                "score": score,
                "reason": ", ".join(reasons),
            }
        )

    remaining_budget = budget - total
    return {
        "recommendations": recommendations,
        "total_price": total,
        "remaining_budget": remaining_budget,
        "selected_categories": [item["product"].category for item in recommendations],
        "ingredient_hints": ingredient_hints,
        "allergen_filters": allergens,
    }
