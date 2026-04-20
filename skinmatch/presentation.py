from urllib.parse import quote


CATEGORY_COLORS = {
    "cleanser": ("#f8e8d8", "#8f5d3f"),
    "toner": ("#f4dff0", "#8a4f86"),
    "serum": ("#e4eefc", "#426899"),
    "moisturizer": ("#e8f3e4", "#4a7d4f"),
    "sunscreen": ("#fff0c9", "#9a6a10"),
    "mask": ("#ece4fb", "#5d4f8a"),
}


def placeholder_image_url(category, brand, name):
    bg, fg = CATEGORY_COLORS.get(category, ("#f0ede8", "#6d5e52"))
    brand_text = (brand or "SkinMatch")[:18]
    name_text = (name or category or "Product")[:26]
    svg = f"""
    <svg xmlns='http://www.w3.org/2000/svg' width='640' height='480'>
      <rect width='100%' height='100%' fill='{bg}'/>
      <rect x='60' y='50' width='520' height='380' rx='42' fill='white' opacity='0.78'/>
      <text x='80' y='150' font-size='28' font-family='Arial, sans-serif' fill='{fg}'>{brand_text}</text>
      <text x='80' y='205' font-size='34' font-weight='700' font-family='Arial, sans-serif' fill='{fg}'>{name_text}</text>
      <text x='80' y='260' font-size='22' font-family='Arial, sans-serif' fill='{fg}'>Category: {category.title()}</text>
      <circle cx='500' cy='145' r='48' fill='{fg}' opacity='0.12'/>
      <circle cx='520' cy='160' r='28' fill='{fg}' opacity='0.18'/>
    </svg>
    """.strip()
    return f"data:image/svg+xml;utf8,{quote(svg)}"
