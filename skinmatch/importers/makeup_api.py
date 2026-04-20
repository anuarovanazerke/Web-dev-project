import json
import ssl
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from urllib.request import urlopen


BASE_URL = "https://makeup-api.herokuapp.com/api/v1/products.json"

PRODUCT_TYPE_CATEGORY_MAP = {
    "cleanser": "cleanser",
    "foundation": "foundation",
    "bronzer": "bronzer",
    "blush": "blush",
    "concealer": "concealer",
}

TAG_CONCERN_MAP = {
    "oil free": "acne",
    "organic": "sensitivity",
    "natural": "sensitivity",
    "purpicks": "sensitivity",
    "ewg verified": "sensitivity",
    "canadian": "dullness",
    "vegan": "sensitivity",
    "gluten free": "sensitivity",
}


def fetch_makeup_products(product_type=None, brand=None, verify_ssl=True):
    params = {}
    if product_type:
        params["product_type"] = product_type
    if brand:
        params["brand"] = brand

    url = BASE_URL
    if params:
        url = f"{url}?{urlencode(params)}"

    context = None
    if not verify_ssl:
        context = ssl._create_unverified_context()

    with urlopen(url, timeout=30, context=context) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_price(raw_price):
    try:
        return Decimal(str(raw_price or "0")).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def map_product_type(product_type):
    normalized = (product_type or "").strip().lower()
    if normalized in PRODUCT_TYPE_CATEGORY_MAP:
        return PRODUCT_TYPE_CATEGORY_MAP[normalized]
    if normalized in {"bb_cc", "cc", "bb"}:
        return "foundation"
    if normalized in {"powder"}:
        return "foundation"
    if normalized in {"lipstick", "lip_gloss", "lip_liner", "mascara", "eyeliner", "eyeshadow"}:
        return "foundation"
    return "serum"


def infer_concerns(product_data):
    tags = [tag.strip().lower() for tag in product_data.get("tag_list") or [] if tag.strip()]
    concerns = []

    for tag in tags:
        concern = TAG_CONCERN_MAP.get(tag)
        if concern and concern not in concerns:
            concerns.append(concern)

    name = (product_data.get("name") or "").lower()
    description = (product_data.get("description") or "").lower()
    text = f"{name} {description}"

    keyword_map = {
        "acne": ["acne", "blemish", "clarifying", "oil control", "mattifying"],
        "wrinkles": ["retinol", "firming", "anti-aging", "peptide"],
        "pigmentation": ["brightening", "vitamin c", "dark spot"],
        "dehydration": ["hydrating", "hyaluronic", "moisture"],
        "sensitivity": ["soothing", "calming", "barrier", "gentle"],
        "dullness": ["glow", "radiance", "illuminating"],
    }

    for concern, keywords in keyword_map.items():
        if any(keyword in text for keyword in keywords) and concern not in concerns:
            concerns.append(concern)

    return ",".join(concerns[:3])


def infer_skin_type(product_data):
    text = f"{product_data.get('name', '')} {product_data.get('description', '')}".lower()
    if any(keyword in text for keyword in ["dry skin", "hydrating", "moisture"]):
        return "dry"
    if any(keyword in text for keyword in ["oily skin", "oil control", "mattifying"]):
        return "oily"
    if any(keyword in text for keyword in ["combination skin", "combo skin"]):
        return "combo"
    if any(keyword in text for keyword in ["normal skin"]):
        return "normal"
    return "all"


def product_from_api(product_data):
    brand = (product_data.get("brand") or "Unknown Brand").strip()[:100]
    name = (product_data.get("name") or "Unnamed product").strip()[:200]
    description = (product_data.get("description") or "").strip()
    price = normalize_price(product_data.get("price"))

    return {
        "brand": brand,
        "name": name,
        "category": map_product_type(product_data.get("product_type")),
        "price": price,
        "recommended_for_skin": infer_skin_type(product_data),
        "concern_focus": infer_concerns(product_data),
        "recommended_for_face_shape": "",
        "description": description[:5000],
        "ingredient_summary": "",
        "image_url": str(product_data.get("api_featured_image") or "").strip(),
        "is_budget_friendly": price > 0 and price <= Decimal("20.00"),
    }
