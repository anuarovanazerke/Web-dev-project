BAD_NAME_FRAGMENTS = [
    "unnamed product",
    "metallica",
    "derma laser 100",
    "eliza jones",
]

BRAND_NORMALIZATION = {
    "la roche-posay": "La Roche-Posay",
    "la roche - posay": "La Roche-Posay",
    "cerave": "CeraVe",
    "garnier ambre solaire,garnier": "Garnier",
    "vasaline": "Vaseline",
    "denéva skincare": "Deneva Skincare",
}

NAME_NORMALIZATION = {
    "retinol serum b3": "Retinol Serum B3",
    "sport face oil-free lotion sunscreen 70": "Sport Face Oil-Free Sunscreen SPF 70",
    "sensitive expert + spf 50+ spay": "Sensitive Expert SPF 50+ Spray",
    "enfant sensitive expert + spf 50+ spay": "Sensitive Expert Kids SPF 50+ Spray",
    "spray solaire": "Sun Spray SPF",
    "dermo protect spf 50+": "Dermo Protect SPF 50+",
    "vaseline deep moisturizer": "Vaseline Deep Moisture",
    "st ives moisturizer": "St. Ives Moisturizer",
    "hidra hialurónico sérum rellenador": "Hyaluronic Filling Serum",
    "lait hydratant": "Hydrating Lotion",
    "serum oil curl perfect": "Curl Perfect Serum",
}

BAD_BRANDS = {
    "unknown brand",
    "extract",
    "hul",
}

BODY_ONLY_FRAGMENTS = [
    "body lotion",
    "body moisturizer",
]

LOW_QUALITY_MASK_FRAGMENTS = [
    "sheet mask",
]


def should_keep_product(product):
    brand = (product.brand or "").strip().lower()
    name = (product.name or "").strip().lower()
    description = (product.description or "").strip().lower()
    joined = f"{name} {description}"

    if not brand or brand in BAD_BRANDS:
        return False

    if any(fragment in joined for fragment in BAD_NAME_FRAGMENTS):
        return False

    if any(fragment in joined for fragment in BODY_ONLY_FRAGMENTS):
        return False

    if product.category == "mask" and any(fragment in joined for fragment in LOW_QUALITY_MASK_FRAGMENTS):
        return False

    if brand.count(",") >= 2:
        return False

    return True


def normalize_product_fields(product):
    brand = (product.brand or "").strip()
    name = (product.name or "").strip()

    normalized_brand = BRAND_NORMALIZATION.get(brand.lower(), brand.title() if brand.islower() else brand)
    normalized_name = NAME_NORMALIZATION.get(name.lower(), name)

    normalized_name = normalized_name.replace("Spf", "SPF").replace("spf", "SPF")
    normalized_name = normalized_name.replace("serum", "Serum") if normalized_name == normalized_name.lower() else normalized_name

    product.brand = normalized_brand[:100]
    product.name = normalized_name[:200]
    return product
