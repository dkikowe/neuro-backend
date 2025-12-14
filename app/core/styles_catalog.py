import random
from typing import Dict, List, Optional, Tuple

# Справочник доступных стилей генерации (интерьерная тематика)
# id используется в API и генерации, name/description идут в выдачу /styles
STYLE_CATALOG: List[Dict[str, object]] = [
    {
        "id": "modern",
        "name": "Современный",
        "description": "Чистые линии, нейтральные оттенки и акцентная подсветка",
        "base_prompt": (
            "interior redesign of the same room using the input photo, keep original room layout and architecture, "
            "do not change wall positions, do not move or add windows, do not move or add doors or passages, "
            "preserve original window and door placement, preserve room proportions and geometry, same camera position and perspective, "
            "modern interior design, clean lines, neutral palette, premium furniture, natural materials, soft indirect LED lighting, "
            "photorealistic textures, high-end architectural interior photography, strict structural preservation, layout locked, geometry locked"
        ),
        "negative_prompt": (
            "extra windows, additional doors, new doorways, open archways, changed room layout, altered architecture, "
            "hallway creation, room expansion, merged rooms, moved windows, moved doors, distorted geometry, broken proportions, "
            "fisheye distortion, unrealistic perspective, duplicate openings, warped walls, missing windows, extra rooms"
        ),
        "variants": {
            "furniture": [
                "sleek modular sofa, marble coffee table, minimal shelving",
                "fabric sofa with rounded edges, wood coffee table, abstract wall art",
                "low-profile modern couch, metal floor lamp, designer armchair",
            ],
            "walls": [
                "smooth grey walls, matte finish",
                "warm beige walls with subtle plaster texture",
                "accent wall with vertical wooden slats",
            ],
            "lighting": [
                "diffused natural daylight, soft shadows",
                "warm evening ambient lighting, cozy atmosphere",
                "neutral LED ceiling spots with soft indirect glow",
            ],
            "camera": [
                "wide-angle shot 18mm, interior photography",
                "35mm natural perspective, architectural photo",
                "angled corner perspective for depth, same camera position",
            ],
        },
    },
    {
        "id": "scandi",
        "name": "Скандинавский",
        "description": "Светлое дерево, белые стены и уютный минимализм",
        "base_prompt": (
            "interior redesign of the same room using the input photo, keep original room layout and architecture, "
            "do not change wall positions, do not move or add windows, do not move or add doors or passages, "
            "preserve original window and door placement, preserve room proportions and geometry, same camera position and perspective, "
            "scandinavian interior design, birch wood furniture, white matte walls, cozy hygge textiles, airy minimal design, natural daylight, "
            "photorealistic render, strict structural preservation, layout locked, geometry locked"
        ),
        "negative_prompt": (
            "extra windows, additional doors, new doorways, open archways, changed room layout, altered architecture, "
            "hallway creation, room expansion, merged rooms, moved windows, moved doors, distorted geometry, broken proportions, "
            "fisheye distortion, unrealistic perspective, duplicate openings, warped walls"
        ),
        "variants": {
            "furniture": [
                "light fabric sofa, knitted blanket, wooden coffee table, simple shelving",
                "rounded scandinavian armchair, woven textures, minimal cabinet",
                "linen curtains, soft pastel pillows, light wood sideboard",
            ],
            "walls": [
                "pure white matte walls",
                "soft warm white with subtle texture",
                "pastel sage accent wall, minimal pattern",
            ],
            "lighting": [
                "bright natural daylight through large windows",
                "soft warm lamp lighting for hygge mood",
                "overcast diffused daylight, gentle shadows",
            ],
            "camera": [
                "wide-angle daylight interior shot 18mm",
                "35mm interior photo, calm centered framing",
                "corner perspective with depth, same camera position",
            ],
        },
    },
    {
        "id": "loft",
        "name": "Лофт",
        "description": "Бетон, кирпич, металл и индустриальная атмосфера",
        "base_prompt": (
            "interior redesign of the same room using the input photo, keep original room layout and architecture, "
            "do not change wall positions, do not move or add windows, do not move or add doors or passages, "
            "preserve original window and door placement, preserve room proportions and geometry, same camera position and perspective, "
            "industrial loft interior design, exposed brick, concrete textures, black metal accents, raw wood surfaces, photorealistic gritty textures, "
            "strict structural preservation, layout locked, geometry locked"
        ),
        "negative_prompt": (
            "extra windows, additional doors, new doorways, open archways, changed room layout, altered architecture, "
            "hallway creation, room expansion, merged rooms, moved windows, moved doors, distorted geometry, broken proportions, "
            "fisheye distortion, unrealistic perspective, duplicate openings, warped walls"
        ),
        "variants": {
            "furniture": [
                "vintage leather sofa, metal coffee table, industrial shelves",
                "raw wood dining table, black steel frames, minimal decor",
                "industrial armchair, arc floor lamp, reclaimed wood console",
            ],
            "walls": [
                "exposed red brick accent wall",
                "raw concrete walls with subtle stains",
                "dark matte paint with metal details",
            ],
            "lighting": [
                "dramatic high-contrast lighting, moody shadows",
                "cold industrial LED strip lighting",
                "warm Edison bulbs with spot highlights",
            ],
            "camera": [
                "ultra wide-angle interior shot 18mm",
                "35mm gritty loft photography",
                "dynamic corner shot, same camera position",
            ],
        },
    },
    {
        "id": "minimalist",
        "name": "Минимализм",
        "description": "Минимум декора и максимум воздуха",
        "base_prompt": (
            "interior redesign of the same room using the input photo, keep original room layout and architecture, "
            "do not change wall positions, do not move or add windows, do not move or add doors or passages, "
            "preserve original window and door placement, preserve room proportions and geometry, same camera position and perspective, "
            "strict minimalist interior design, monochrome palette, hidden storage, open breathable space, matte textures, "
            "ultra-clean lines, photorealistic modern minimalism, strict structural preservation, layout locked, geometry locked"
        ),
        "negative_prompt": (
            "extra windows, additional doors, new doorways, open archways, changed room layout, altered architecture, "
            "hallway creation, room expansion, merged rooms, moved windows, moved doors, distorted geometry, broken proportions, "
            "fisheye distortion, unrealistic perspective, duplicate openings, warped walls, clutter, messy decor"
        ),
        "variants": {
            "furniture": [
                "low-profile sofa, no visible decor, minimal coffee table",
                "floating shelves, pure geometric forms, hidden storage",
                "minimal round table, slim chairs, clean surfaces",
            ],
            "walls": [
                "pure white matte walls",
                "soft light grey walls, subtle texture",
                "monochrome warm beige minimal finish",
            ],
            "lighting": [
                "clean diffused daylight, soft shadows",
                "soft indirect LED wall lighting",
                "neutral bright ceiling lighting, minimal fixtures",
            ],
            "camera": [
                "symmetrical centered shot, architectural minimalism",
                "wide-angle emphasizing empty space 18mm",
                "side perspective highlighting geometry, same camera position",
            ],
        },
    },
    {
        "id": "classic",
        "name": "Классический",
        "description": "Молдинги, симметрия и благородные материалы",
        "base_prompt": (
            "interior redesign of the same room using the input photo, keep original room layout and architecture, "
            "do not change wall positions, do not move or add windows, do not move or add doors or passages, "
            "preserve original window and door placement, preserve room proportions and geometry, same camera position and perspective, "
            "classic interior design, wall mouldings, elegant symmetry, marble and wood materials, premium furniture, soft ambient lighting, "
            "photorealistic elegant atmosphere, strict structural preservation, layout locked, geometry locked"
        ),
        "negative_prompt": (
            "extra windows, additional doors, new doorways, open archways, changed room layout, altered architecture, "
            "hallway creation, room expansion, merged rooms, moved windows, moved doors, distorted geometry, broken proportions, "
            "fisheye distortion, unrealistic perspective, duplicate openings, warped walls, modern industrial pipes"
        ),
        "variants": {
            "furniture": [
                "velvet sofa, carved wood table, subtle gold accents",
                "classic armchairs, elegant console table, framed art",
                "traditional sofa set, marble-top side tables, refined decor",
            ],
            "walls": [
                "cream walls with decorative mouldings",
                "light pastel walls with classic panels",
                "soft beige walls with elegant trim and pilasters",
            ],
            "lighting": [
                "warm chandelier lighting, soft glow",
                "classic wall sconces with warm light",
                "soft golden ambient lighting, refined shadows",
            ],
            "camera": [
                "symmetrical classical view, centered framing",
                "wide-angle 18mm capturing full layout",
                "slightly elevated perspective, same camera position",
            ],
        },
    },
    {
        "id": "japandi",
        "name": "Япанди",
        "description": "Японский минимализм и скандинавский уют",
        "base_prompt": (
            "interior redesign of the same room using the input photo, keep original room layout and architecture, "
            "do not change wall positions, do not move or add windows, do not move or add doors or passages, "
            "preserve original window and door placement, preserve room proportions and geometry, same camera position and perspective, "
            "japandi interior design, japanese minimalism and scandinavian calm, natural wood and stone textures, low-profile furniture, "
            "soft earthy tones, calm zen atmosphere, uncluttered space, photorealistic render, strict structural preservation, layout locked, geometry locked"
        ),
        "negative_prompt": (
            "extra windows, additional doors, new doorways, open archways, changed room layout, altered architecture, "
            "hallway creation, room expansion, merged rooms, moved windows, moved doors, distorted geometry, broken proportions, "
            "fisheye distortion, unrealistic perspective, duplicate openings, warped walls, clutter"
        ),
        "variants": {
            "furniture": [
                "low japanese-style table, linen sofa, minimal decor",
                "natural wood bench with soft cushions, simple shelving",
                "bamboo shelving, stone vase decor, low profile seating",
            ],
            "walls": [
                "warm earthy beige walls, soft plaster texture",
                "neutral off-white with subtle wabi-sabi imperfections",
                "light wood panel accent, natural textures",
            ],
            "lighting": [
                "soft warm natural daylight, gentle shadows",
                "diffused evening light for zen mood",
                "soft indirect lighting, calm atmosphere",
            ],
            "camera": [
                "calm centered zen shot, 35mm interior photo",
                "wide-angle natural perspective 18mm",
                "minimal corner view with depth, same camera position",
            ],
        },
    },
    {
        "id": "luxury-modern",
        "name": "Современная роскошь",
        "description": "Мрамор, латунь и премиальный свет без классических элементов",
        "base_prompt": (
            "interior redesign of the same room using the input photo, keep original room layout and architecture, "
            "do not change wall positions, do not move or add windows, do not move or add doors or passages, "
            "preserve original window and door placement, preserve room proportions and geometry, same camera position and perspective, "
            "luxury modern interior design, marble surfaces, brass accents, premium furniture, rich textures, soft golden ambient lighting, "
            "cinematic moody shadows, high-end architectural interior photography, no classic mouldings, strict structural preservation, layout locked, geometry locked"
        ),
        "negative_prompt": (
            "extra windows, additional doors, new doorways, open archways, changed room layout, altered architecture, "
            "hallway creation, room expansion, merged rooms, moved windows, moved doors, distorted geometry, broken proportions, "
            "fisheye distortion, unrealistic perspective, duplicate openings, warped walls, classic mouldings, ornate classic decor"
        ),
        "variants": {
            "furniture": [
                "premium velvet sofa with brass legs, designer armchair",
                "large modular sofa, marble coffee table, luxury rug",
                "dark wood console, sculptural decor objects, statement chair",
            ],
            "walls": [
                "dark charcoal walls with subtle texture",
                "marble accent wall behind seating area",
                "soft suede-like wall finish with warm tones",
            ],
            "lighting": [
                "warm golden ambient lighting, indirect glow",
                "cinematic side lighting with strong contrast",
                "luxury LED contour illumination, soft reflections",
            ],
            "camera": [
                "architectural digest style angle, 35mm",
                "wide cinematic framing 18mm",
                "centered high-end composition, same camera position",
            ],
        },
    },
    {
        "id": "art-deco",
        "name": "Ар-деко",
        "description": "Геометрия, насыщенные оттенки и гламурная роскошь",
        "base_prompt": (
            "interior redesign of the same room using the input photo, keep original room layout and architecture, "
            "do not change wall positions, do not move or add windows, do not move or add doors or passages, "
            "preserve original window and door placement, preserve room proportions and geometry, same camera position and perspective, "
            "art deco interior design, geometric patterns, rich saturated colors, velvet furniture, brass details, glossy finishes, glamorous 1920s aesthetic, "
            "photorealistic render, strict structural preservation, layout locked, geometry locked"
        ),
        "negative_prompt": (
            "extra windows, additional doors, new doorways, open archways, changed room layout, altered architecture, "
            "hallway creation, room expansion, merged rooms, moved windows, moved doors, distorted geometry, broken proportions, "
            "fisheye distortion, unrealistic perspective, duplicate openings, warped walls"
        ),
        "variants": {
            "furniture": [
                "curved velvet sofa with brass legs, geometric side tables",
                "luxury armchairs with gold accents, glossy coffee table",
                "symmetrical seating arrangement, decorative console table",
            ],
            "walls": [
                "deep emerald green walls with gold lines",
                "rich burgundy walls with geometric patterns",
                "glossy neutral walls with brass inlays",
            ],
            "lighting": [
                "warm glam chandelier lighting",
                "spotlights with soft shadows, reflective highlights",
                "gold wall sconces with warm glow",
            ],
            "camera": [
                "symmetrical glamorous view, centered framing",
                "wide-angle opulent framing 18mm",
                "dramatic diagonal angle, same camera position",
            ],
        },
    },
    {
        "id": "mediterranean",
        "name": "Средиземноморский",
        "description": "Арки, штукатурка, терракота и солнечная атмосфера",
        "base_prompt": (
            "interior redesign of the same room using the input photo, keep original room layout and architecture, "
            "do not change wall positions, do not move or add windows, do not move or add doors or passages, "
            "preserve original window and door placement, preserve room proportions and geometry, same camera position and perspective, "
            "mediterranean interior design, white stucco walls, arches, terracotta tiles, natural fabrics, warm coastal sunlight, "
            "photorealistic warm southern atmosphere, strict structural preservation, layout locked, geometry locked"
        ),
        "negative_prompt": (
            "extra windows, additional doors, new doorways, open archways, changed room layout, altered architecture, "
            "hallway creation, room expansion, merged rooms, moved windows, moved doors, distorted geometry, broken proportions, "
            "fisheye distortion, unrealistic perspective, duplicate openings, warped walls"
        ),
        "variants": {
            "furniture": [
                "rustic wooden bench with linen cushions, natural decor",
                "linen sofa with neutral pillows, wicker accents",
                "wooden table, clay pots, woven textures",
            ],
            "walls": [
                "white stucco walls with subtle texture",
                "soft sand-colored plaster finish",
                "arched niches with minimal decor",
            ],
            "lighting": [
                "bright warm coastal sunlight, soft shadows",
                "soft afternoon golden light",
                "gentle natural window shadows, warm atmosphere",
            ],
            "camera": [
                "wide mediterranean open view 18mm",
                "centered coastal-inspired framing 35mm",
                "warm corner angle, same camera position",
            ],
        },
    },
]

# Наборы для валидации и быстрого доступа
STYLE_IDS = {style["id"] for style in STYLE_CATALOG}

# Пресет для Stability AI — для интерьерных визуализаций оставляем фотореализм
STYLE_PRESET = "photographic"


def get_public_styles() -> List[Dict[str, str]]:
    """Вернуть список стилей без промптов для отдачи наружу."""
    return [
        {key: style[key] for key in ("id", "name", "description")}
        for style in STYLE_CATALOG
    ]


def _pick_variant(style: Dict[str, object], key: str) -> Optional[str]:
    """Вернуть случайный вариант из указанной группы или None, если нет данных."""
    variants = style.get("variants") or {}
    options = variants.get(key) if isinstance(variants, dict) else None
    if not options:
        return None
    return random.choice(options)  # type: ignore[arg-type]


def build_style_prompt(style_id: str) -> Tuple[Optional[str], Optional[Dict[str, Optional[str]]]]:
    """
    Собрать промпт для стиля с добавлением случайных вариаций по мебели, стенам, свету и камере.
    Возвращает (prompt, meta) или (None, None), если стиль не найден.
    """
    style_id = style_id.lower()
    style = next((s for s in STYLE_CATALOG if s["id"] == style_id), None)
    if not style:
        return None, None

    furniture = _pick_variant(style, "furniture")
    walls = _pick_variant(style, "walls")
    lighting = _pick_variant(style, "lighting")
    camera = _pick_variant(style, "camera")

    variant_parts = [
        f"Furniture: {furniture}" if furniture else None,
        f"Walls: {walls}" if walls else None,
        f"Lighting: {lighting}" if lighting else None,
        f"Camera: {camera}" if camera else None,
    ]
    variant_text = ". ".join(part for part in variant_parts if part)

    base_prompt = style.get("base_prompt") or ""
    negative_prompt = style.get("negative_prompt") or ""

    prompt_parts = [base_prompt]
    if variant_text:
        prompt_parts.append(variant_text)
    if negative_prompt:
        prompt_parts.append(f"Negative prompt: {negative_prompt}")

    prompt = ". ".join(part for part in prompt_parts if part)

    meta = {
        "style_id": style_id,
        "base_prompt": str(base_prompt),
        "furniture": furniture,
        "walls": walls,
        "lighting": lighting,
        "camera": camera,
        "negative_prompt": str(negative_prompt) if negative_prompt else None,
    }
    return prompt, meta