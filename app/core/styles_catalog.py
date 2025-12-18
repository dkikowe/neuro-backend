import random
from typing import Dict, List, Optional, Tuple

# Настройки по умолчанию для промптов
PROMPT_JOINER = ". "
VARIANT_JOINER = ", "
LENS_MM = "28-35"
STYLE_PRESET = "photographic"

PROMPT_TEMPLATE = {
    "global_base_core": (
        "interior redesign of the same room using the input photo, this is an interior redesign not a new room, "
        "keep original spatial layout and room boundaries, architecture must remain exactly the same, "
        "walls ceiling floor structure doors and windows are fixed, do not change wall positions, do not move or add windows, "
        "do not move or add doors or passages, no architectural creativity, preserve original window and door placement, "
        "preserve room proportions and geometry, keep existing fixed elements in place, same camera position and perspective, "
        f"real-world furniture proportions, commercially available furniture, balanced furniture density, clear walking paths, "
        f"shot on a real camera, {LENS_MM}mm lens, interior photography, architectural digest style, natural color grading, "
        "true-to-life colors, realistic materials and textures, subtle surface imperfections, structural consistency, "
        "strict structural preservation, layout locked, geometry locked"
    ),
    "global_negative": (
        "extra windows, new windows, moved windows, additional doors, new doorways, arches as openings, archways as openings, portals, "
        "hallway creation, room expansion, merged rooms, altered architecture, distorted geometry, unrealistic proportions, "
        "fisheye, ultra wide, extreme perspective, CGI look, 3D render look, overprocessed, oversharpened, oversaturated colors, "
        "clutter, messy composition, overdecorated, unrealistic furniture scale, duplicate openings, warped walls, missing windows, extra rooms"
    ),
    "design_variation_block": (
        "wall finishes may vary: paint or plaster or microcement or subtle wood panels, no structural wall changes, no new niches or openings, "
        "floor finish variation: wide plank wood flooring or stone tiles or microcement, realistic joints and seams, "
        "ceiling design may include: smooth painted ceiling or subtle recessed lighting or minimal ceiling details, no change to ceiling height, "
        "layered lighting design: ambient light plus accent light plus soft indirect light, natural daylight balanced with artificial lighting, "
        "realistic shadow behavior"
    ),
}

ROOM_CONTEXT = {
    "living_room": {
        "base": (
            "this image shows a living room, designed for relaxation and socializing, only living room furniture: "
            "sofa, armchairs, coffee table, media console, side tables, lamps, rugs, curtains, "
            "no bedroom furniture, no kitchen appliances, no bathroom fixtures"
        ),
        "negative": (
            "bed, mattress, bunk bed, crib, kitchen stove, oven, refrigerator, sink, dishwasher, bathtub, shower, toilet, vanity sink, "
            "office workstation, standing desk"
        ),
    },
    "bedroom": {
        "base": (
            "this image shows a bedroom, designed for sleeping and rest, only bedroom furniture: bed, nightstands, wardrobe, dresser, "
            "soft seating, lamps, curtains, no kitchen appliances, no bathroom fixtures, no large living room sectional sofa"
        ),
        "negative": (
            "kitchen stove, oven, refrigerator, sink, dishwasher, bathtub, shower, toilet, vanity sink, large sectional sofa, "
            "media wall built for living room, bar counter"
        ),
    },
    "kitchen": {
        "base": (
            "this image shows a kitchen, designed for cooking and dining, only kitchen and dining furniture: cabinetry, countertops, backsplash, "
            "dining table and chairs, kitchen island if already present, keep existing kitchen layout fixed, keep sink stove cooktop oven "
            "refrigerator countertop positions unchanged if visible, no bedroom furniture, no living room sofa, no bathroom fixtures"
        ),
        "negative": (
            "bed, mattress, bunk bed, crib, sectional sofa, living room coffee table set, bathtub, shower, toilet, vanity sink, office workstation"
        ),
    },
    "bathroom": {
        "base": (
            "this image shows a bathroom, designed for hygiene and relaxation, only bathroom fixtures and furniture: vanity, sink, shower, "
            "bathtub, toilet, mirrors, towel storage, keep plumbing fixtures in the same place if visible, no living room furniture, "
            "no kitchen cabinetry, no bed"
        ),
        "negative": (
            "sofa, sectional sofa, coffee table, dining table, kitchen stove, refrigerator, bed, mattress, office desk"
        ),
    },
    "home_office": {
        "base": (
            "this image shows a home office, designed for work and productivity, only office-appropriate furniture: desk, ergonomic chair, "
            "shelves, storage, task lighting, no bed, no kitchen appliances, no bathroom fixtures"
        ),
        "negative": (
            "bed, mattress, bathtub, shower, toilet, kitchen stove, refrigerator, sink, sectional sofa"
        ),
    },
}

# Справочник доступных стилей генерации
STYLE_CATALOG: List[Dict[str, object]] = [
    {
        "id": "soft-minimal",
        "name": "Софт-минимализм",
        "description": "Светлый минимализм с мягкими формами и спокойным светом",
        "style_prompt": (
            "soft minimal interior design, ultra light palette, creamy whites, rounded furniture, soft upholstery, minimal decor, "
            "diffused daylight, airy calm atmosphere"
        ),
        "variants": {
            "furniture": [
                "rounded modular sofa, low oak coffee table, soft boucle lounge chair",
                "slim console, light fabric sofa, sculptural side table",
                "low-profile sectional, minimal shelves, plush area rug",
            ],
            "walls": [
                "warm white limewash walls, smooth matte finish",
                "very light beige plaster texture",
                "soft off-white paint with subtle texture",
            ],
            "floors": [
                "wide plank light oak flooring",
                "microcement floor in warm light gray",
                "light stone tiles with subtle joints",
            ],
            "ceiling": [
                "smooth white ceiling with subtle recessed lighting",
                "minimal ceiling with hidden cove lighting",
                "simple ceiling with discreet spotlights",
            ],
            "lighting": [
                "diffused north-facing daylight, soft shadows",
                "hidden cove lighting with warm temperature",
                "neutral ceiling spots with dimmed output",
            ],
            "camera": [
                "35mm calm frontal shot",
                "32mm slight angle for depth",
                "30mm centered symmetrical framing",
            ],
        },
    },
    {
        "id": "warm-modern",
        "name": "Тёплый модерн",
        "description": "Тёплый современный стиль с ощущением уюта и баланса",
        "style_prompt": (
            "warm modern interior, warm beige and caramel tones, natural wood and stone, tactile fabrics, elegant modern furniture, "
            "soft warm lighting, cozy calm mood"
        ),
        "variants": {
            "furniture": [
                "fabric sofa in warm beige, walnut coffee table, woven pouf",
                "caramel-toned armchairs, travertine side table, soft rug",
                "modern wood console, linen sofa, bronze floor lamp",
            ],
            "walls": [
                "warm beige paint, soft matte",
                "light sand-toned plaster",
                "neutral wall with thin wood slats accent",
            ],
            "floors": [
                "walnut tone wood flooring",
                "warm stone tiles with natural variation",
                "microcement floor in warm greige",
            ],
            "ceiling": [
                "smooth ceiling with warm recessed downlights",
                "minimal ceiling with indirect perimeter lighting",
                "clean ceiling with subtle linear lighting",
            ],
            "lighting": [
                "warm indirect ceiling wash",
                "table lamps with fabric shades, low intensity",
                "window daylight with light curtains, gentle shadows",
            ],
            "camera": [
                "35mm eye-level interior shot",
                "32mm angle capturing seating group",
                "30mm centered view with balanced composition",
            ],
        },
    },
    {
        "id": "neo-japandi",
        "name": "Нео-Япанди",
        "description": "Современный Japandi с дисциплиной и дзен-балансом",
        "style_prompt": (
            "neo japandi interior, japanese minimalism with scandinavian precision, low profile furniture, matte wood, stone textures, "
            "controlled warm lighting, disciplined composition"
        ),
        "variants": {
            "furniture": [
                "low oak platform sofa, linen cushions, minimal cabinet",
                "ash wood bench, stone side table, paper lantern lamp",
                "low coffee table, woven pouf, calm storage",
            ],
            "walls": [
                "soft greige plaster with subtle texture",
                "light oak panel accent, matte finish",
                "neutral off-white walls, calm tone",
            ],
            "floors": [
                "light oak wood flooring",
                "warm stone flooring with matte finish",
                "microcement floor in soft greige",
            ],
            "ceiling": [
                "smooth ceiling with minimal recessed lighting",
                "ceiling with subtle indirect warm lighting",
                "clean ceiling with discreet spotlights",
            ],
            "lighting": [
                "controlled warm directional sconces",
                "soft window daylight filtered by linen curtains",
                "hidden low-level indirect lighting",
            ],
            "camera": [
                "32mm calm angle showing depth",
                "35mm straight-on disciplined framing",
                "30mm slight diagonal with leading lines",
            ],
        },
    },
    {
        "id": "organic-modern",
        "name": "Органичный модерн",
        "description": "Природные формы и биоморфный современный дизайн",
        "style_prompt": (
            "organic modern interior, sculptural furniture, soft curves, natural stone and wood, earthy tones, organic flow, soft shadows, "
            "calm premium atmosphere"
        ),
        "variants": {
            "furniture": [
                "sculptural boucle sofa, pebble coffee table, curved sideboard",
                "rounded edge dining table, soft leather chairs, organic decor",
                "stone pedestal side table, curved lounge chair, wool rug",
            ],
            "walls": [
                "warm clay-toned plaster with soft variation",
                "light taupe microcement, matte",
                "pale sand paint with subtle movement",
            ],
            "floors": [
                "wide plank natural oak flooring",
                "stone tiles in warm neutral tones",
                "microcement floor with soft mineral texture",
            ],
            "ceiling": [
                "smooth ceiling with subtle recessed lighting",
                "minimal ceiling with indirect lighting wash",
                "clean ceiling with discreet linear lighting",
            ],
            "lighting": [
                "soft bounced light from wall washers",
                "warm dimmable frosted glass pendants",
                "natural daylight with sheer curtains, gentle falloff",
            ],
            "camera": [
                "32mm angle highlighting curves",
                "35mm balanced composition, eye level",
                "30mm slight corner view for flow",
            ],
        },
    },
    {
        "id": "wabi-sabi-modern",
        "name": "Ваби-саби модерн",
        "description": "Современный wabi-sabi с фактурой и глубиной",
        "style_prompt": (
            "wabi sabi modern interior, textured plaster walls, imperfect surfaces, muted earth tones, aged wood, poetic minimalism, "
            "moody natural light"
        ),
        "variants": {
            "furniture": [
                "aged wood bench, linen cushions, ceramic decor",
                "low sofa in muted linen, rough-hewn coffee table",
                "stone stool, vintage sideboard, woven rug",
            ],
            "walls": [
                "hand-troweled clay plaster, visible texture",
                "warm greige limewash with patina",
                "soft earth-toned paint with natural variation",
            ],
            "floors": [
                "matte stone tiles with natural imperfections",
                "wide plank aged oak flooring",
                "microcement floor with subtle wear",
            ],
            "ceiling": [
                "smooth ceiling with minimal recessed lighting",
                "simple ceiling with warm indirect lighting",
                "clean ceiling with discreet spots",
            ],
            "lighting": [
                "moody side light, natural shadows",
                "paper lantern diffused glow",
                "narrow beam spot highlighting texture",
            ],
            "camera": [
                "35mm intimate eye-level view",
                "32mm diagonal showing texture depth",
                "30mm calm centered frame",
            ],
        },
    },
    {
        "id": "neo-scandinavian",
        "name": "Нео-скандинавский",
        "description": "Чистый и мягкий скандинавский стиль нового поколения",
        "style_prompt": (
            "neo scandinavian interior, light oak wood, soft gray and white palette, functional furniture, clean geometry, abundant natural daylight"
        ),
        "variants": {
            "furniture": [
                "light oak dining table, soft fabric chairs, minimal sideboard",
                "gray fabric sofa, pale wood coffee table, simple shelves",
                "linen curtains, pastel cushions, oak console",
            ],
            "walls": [
                "bright white matte walls",
                "very light gray paint, smooth",
                "white walls with subtle oak trim detail",
            ],
            "floors": [
                "light oak flooring with natural grain",
                "whitewashed wood flooring",
                "light stone-look tiles with minimal joints",
            ],
            "ceiling": [
                "smooth ceiling with neutral recessed downlights",
                "clean ceiling with subtle indirect lighting",
                "simple ceiling with discreet spotlights",
            ],
            "lighting": [
                "abundant daylight through sheer curtains",
                "neutral ceiling spots, low intensity",
                "floor lamp with soft white shade",
            ],
            "camera": [
                "35mm airy front view",
                "32mm corner angle to show depth",
                "30mm centered composition, calm",
            ],
        },
    },
    {
        "id": "monochrome-premium",
        "name": "Премиальный монохром",
        "description": "Премиальный монохром с архитектурным светом",
        "style_prompt": (
            "monochrome premium interior, grayscale palette, tonal design, luxury materials, deep shadows, soft highlights, cinematic lighting, "
            "minimalist composition"
        ),
        "variants": {
            "furniture": [
                "charcoal sofa, black stone coffee table, chrome accents",
                "gray velvet lounge chair, smoked glass side table",
                "graphite cabinetry, minimal shelving, metal floor lamp",
            ],
            "walls": [
                "soft gray paint, low sheen",
                "dark charcoal accent wall, matte",
                "microcement gray wall with fine texture",
            ],
            "floors": [
                "dark oak flooring with matte finish",
                "graphite stone tiles with subtle joints",
                "microcement floor in medium gray",
            ],
            "ceiling": [
                "smooth ceiling with subtle recessed lighting",
                "clean ceiling with linear accent lighting",
                "minimal ceiling with indirect wash",
            ],
            "lighting": [
                "architectural grazing light, strong contrast",
                "soft ceiling wash, neutral temperature",
                "accent spots highlighting art, dimmed",
            ],
            "camera": [
                "35mm cinematic framing",
                "32mm moody angled shot",
                "30mm centered high-contrast view",
            ],
        },
    },
    {
        "id": "soft-brutalism",
        "name": "Софт-брутализм",
        "description": "Архитектурный брутализм с мягкой подачей",
        "style_prompt": (
            "soft brutalism interior, exposed concrete textures, solid architectural forms, minimal furniture with softened edges, "
            "neutral gray and warm stone tones, calm architectural atmosphere, soft diffused lighting"
        ),
        "variants": {
            "furniture": [
                "blocky sofa with rounded edges, concrete coffee table",
                "leather lounge chair, stone side table, minimal shelving",
                "low platform seating, metal accents, wool rug",
            ],
            "walls": [
                "light concrete texture, subtle formwork lines",
                "smooth gray plaster with mineral look",
                "concrete finish with warm undertone",
            ],
            "floors": [
                "microcement floor with mineral texture",
                "stone tiles in warm gray",
                "dark matte wood flooring for contrast",
            ],
            "ceiling": [
                "clean ceiling with linear neutral lighting",
                "minimal ceiling with indirect lighting wash",
                "smooth ceiling with discreet spots",
            ],
            "lighting": [
                "soft diffused wall washing",
                "linear ceiling light with neutral tone",
                "daylight with mild shadow, no harsh contrast",
            ],
            "camera": [
                "35mm architectural view",
                "32mm angle emphasizing massing",
                "30mm frontal shot, controlled perspective",
            ],
        },
    },
    {
        "id": "modern-mediterranean",
        "name": "Современный средиземноморский",
        "description": "Современный средиземноморский стиль с солнечным настроением",
        "style_prompt": (
            "modern mediterranean interior, limewashed walls, sandy tones, natural stone, linen textiles, sunlit atmosphere, warm southern mood, "
            "arched decor elements only (arched mirror or arched niche decor), no new openings"
        ),
        "variants": {
            "furniture": [
                "linen slipcover sofa, rustic wood coffee table, woven baskets",
                "light wood dining set, ceramic vases, jute rug",
                "rattan chair, stone side table, linen cushions",
            ],
            "walls": [
                "white limewash with gentle variation",
                "soft sand-colored plaster",
                "pale beige stucco, matte",
            ],
            "floors": [
                "light stone tiles with warm undertone",
                "terracotta-look tiles (no pattern distortion)",
                "wide plank light oak flooring",
            ],
            "ceiling": [
                "smooth ceiling with warm recessed lighting",
                "simple ceiling with subtle indirect warm light",
                "clean ceiling with discreet spotlights",
            ],
            "lighting": [
                "warm coastal daylight, soft shadows",
                "sheer curtains diffusing sun, golden tone",
                "neutral recessed lights, low output",
            ],
            "camera": [
                "35mm bright frontal view",
                "32mm relaxed corner angle",
                "30mm centered sunny composition",
            ],
        },
    },
    {
        "id": "design-hotel",
        "name": "Дизайн-отель",
        "description": "Интерьер как в дизайнерском бутик-отеле",
        "style_prompt": (
            "design hotel interior, curated furniture, statement lighting, refined materials, neutral palette with accents, "
            "elegant hotel-like composition, boutique hotel mood, no architectural changes"
        ),
        "variants": {
            "furniture": [
                "curated lounge chairs, marble coffee table, designer sofa",
                "velvet seating, brass side tables, custom millwork look",
                "sculptural accent chair, stone console, layered textiles",
            ],
            "walls": [
                "panel-like wall finish (decor only), neutral tone",
                "smooth taupe paint with framed art",
                "dark accent wall with integrated light strip (no new openings)",
            ],
            "floors": [
                "dark oak flooring with matte finish",
                "stone tiles with premium grout lines",
                "microcement floor with subtle sheen",
            ],
            "ceiling": [
                "smooth ceiling with warm dim downlights",
                "minimal ceiling with linear accent lighting",
                "clean ceiling with discreet spots",
            ],
            "lighting": [
                "statement pendant, warm dim light",
                "wall washers with soft highlights",
                "table lamps with frosted glass, cozy glow",
            ],
            "camera": [
                "35mm hotel-lobby style framing",
                "32mm angle showcasing seating cluster",
                "30mm centered boutique atmosphere",
            ],
        },
    },
]

# Наборы для валидации и быстрого доступа
STYLE_IDS = {style["id"] for style in STYLE_CATALOG}

# Пресет для Stability AI — для интерьерных визуализаций оставляем фотореализм
STYLE_PRESET = STYLE_PRESET


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


def build_style_prompt(
    style_id: str,
    room_type: Optional[str] = None,
    room_negative: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Optional[str]]]]:
    """
    Собрать промпт для стиля с добавлением случайных вариаций по мебели, стенам, свету и камере.
    Возвращает (positive_prompt, negative_prompt, meta) или (None, None, None), если стиль не найден.
    """
    style_id = style_id.lower()
    style = next((s for s in STYLE_CATALOG if s["id"] == style_id), None)
    if not style:
        return None, None, None

    furniture = _pick_variant(style, "furniture")
    walls = _pick_variant(style, "walls")
    floors = _pick_variant(style, "floors")
    ceiling = _pick_variant(style, "ceiling")
    lighting = _pick_variant(style, "lighting")
    camera = _pick_variant(style, "camera")

    variant_parts = [
        furniture,
        walls,
        floors,
        ceiling,
        lighting,
        camera,
    ]
    variant_text = VARIANT_JOINER.join(part for part in variant_parts if part)

    style_prompt = style.get("style_prompt") or ""
    design_block = PROMPT_TEMPLATE["design_variation_block"]
    global_base = PROMPT_TEMPLATE["global_base_core"]
    global_negative = PROMPT_TEMPLATE["global_negative"]

    room_base = None
    if room_type and room_type in ROOM_CONTEXT:
        room_base = ROOM_CONTEXT[room_type]["base"]
        room_negative_val = ROOM_CONTEXT[room_type].get("negative")
    else:
        room_base = None
        room_negative_val = None

    # Positive
    positive_parts = []
    if room_base:
        positive_parts.append(room_base)
    positive_parts.append(global_base)
    if style_prompt:
        positive_parts.append(style_prompt)
    positive_parts.append(design_block)
    if variant_text:
        positive_parts.append(variant_text)

    positive_prompt = PROMPT_JOINER.join(part for part in positive_parts if part)

    # Negative
    negatives = [global_negative]
    if room_negative_val:
        negatives.append(room_negative_val)
    if room_negative:
        negatives.append(room_negative)
    full_negative = ", ".join([n for n in negatives if n])

    meta = {
        "style_id": style_id,
        "global_base": global_base,
        "style_prompt": str(style_prompt),
        "furniture": furniture,
        "walls": walls,
        "floors": floors,
        "ceiling": ceiling,
        "lighting": lighting,
        "camera": camera,
        "negative_prompt": str(full_negative) if full_negative else None,
        "room_type": room_type,
    }
    return positive_prompt, full_negative, meta