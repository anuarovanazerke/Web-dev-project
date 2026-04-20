import json
import ssl
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from urllib.request import urlopen

from skinmatch.catalog import SKINCARE_CATEGORIES


BASE_URL = "https://world.openbeautyfacts.org/cgi/search.pl"
SEARCH_TERMS = ["cleanser", "toner", "serum", "moisturizer", "sunscreen", "face mask"]


def fetch_open_beauty_facts(search_term, page_size=25, verify_ssl=True):
    params = {
        "search_terms": search_term,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": page_size,
    }
    url = f"{BASE_URL}?{urlencode(params)}"
    context = None
    if not verify_ssl:
        context = ssl._create_unverified_context()

    with urlopen(url, timeout=30, context=context) as response:
        return json.loads(response.read().decode("utf-8")).get("products", [])


def normalize_price(product_data):
    stores_tags = product_data.get("stores_tags") or []
    raw_price = (
        product_data.get("price")
        or product_data.get("price_value")
        or (stores_tags[0] if stores_tags else None)
    )
    try:
        return Decimal(str(raw_price or "0")).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def map_category(search_term, product_data):
    text = (
        f"{product_data.get('product_name', '')} "
        f"{product_data.get('generic_name', '')} "
        f"{' '.join(product_data.get('categories_tags', []) or [])}"
    ).lower()

    if "sunscreen" in text or "spf" in text:
        return "sunscreen"
    if "toner" in text:
        return "toner"
    if "serum" in text or "ampoule" in text:
        return "serum"
    if "mask" in text:
        return "mask"
    if "cream" in text or "moistur" in text or "lotion" in text:
        return "moisturizer"
    if "cleanser" in text or "wash" in text or "gel" in text or "foam" in text:
        return "cleanser"

    fallback = search_term.lower().replace("face ", "")
    return fallback if fallback in SKINCARE_CATEGORIES else "serum"


def infer_skin_type(product_data):
    text = (
        f"{product_data.get('product_name', '')} "
        f"{product_data.get('generic_name', '')} "
        f"{product_data.get('ingredients_text_en', '')}"
    ).lower()
    if any(keyword in text for keyword in ["dry skin", "hydrating", "moisturizing", "ceramide"]):
        return "dry"
    if any(keyword in text for keyword in ["oily skin", "salicylic", "niacinamide", "sebum"]):
        return "oily"
    if "combination skin" in text:
        return "combo"
    if "normal skin" in text:
        return "normal"
    return "all"


def infer_concerns(product_data):
    text = (
        f"{product_data.get('product_name', '')} "
        f"{product_data.get('generic_name', '')} "
        f"{product_data.get('ingredients_text_en', '')}"
    ).lower()

    mapping = {
        "acne": ["acne", "blemish", "salicylic", "niacinamide"],
        "rosacea": ["redness", "rosacea", "calming"],
        "wrinkles": ["retinol", "firming", "anti-aging", "peptide"],
        "pigmentation": ["vitamin c", "brightening", "dark spot"],
        "dehydration": ["hyaluronic", "hydrating", "moisturizing"],
        "sensitivity": ["gentle", "soothing", "barrier", "centella"],
        "dullness": ["glow", "radiance", "brightening"],
        "pores": ["pore", "niacinamide", "bha"],
    }

    concerns = [name for name, keywords in mapping.items() if any(keyword in text for keyword in keywords)]
    return ",".join(concerns[:3])


def product_from_obf(search_term, product_data):
    brands_tags = product_data.get("brands_tags") or []
    brand = product_data.get("brands") or (brands_tags[0] if brands_tags else "Unknown Brand")
    name = product_data.get("product_name") or product_data.get("generic_name") or "Unnamed product"
    description = product_data.get("generic_name_en") or product_data.get("generic_name") or ""
    ingredient_summary = product_data.get("ingredients_text_en") or product_data.get("ingredients_text") or ""
    price = normalize_price(product_data)
    if price <= 0:
        price = Decimal("19.90")

    return {
        "brand": str(brand).strip()[:100],
        "name": str(name).strip()[:200],
        "category": map_category(search_term, product_data),
        "price": price,
        "recommended_for_skin": infer_skin_type(product_data),
        "concern_focus": infer_concerns(product_data),
        "recommended_for_face_shape": "",
        "description": str(description).strip()[:5000],
        "ingredient_summary": str(ingredient_summary).strip()[:5000],
        "image_url": str(product_data.get("image_front_url") or product_data.get("image_url") or "").strip(),
        "is_budget_friendly": price <= Decimal("20.00"),
    }
