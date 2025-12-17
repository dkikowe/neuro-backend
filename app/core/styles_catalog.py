import random
from typing import Dict, List, Optional, Tuple

# Глобальные подсказки для всех стилей
GLOBAL_BASE_PROMPT = (
    "interior redesign of the same room using the input photo, this is an interior redesign not a new room, "
    "keep original spatial layout and room boundaries, architecture must remain exactly the same, "
    "walls ceiling floor doors and windows are fixed, do not change wall positions, do not move or add windows, "
    "do not move or add doors or passages, no architectural creativity, preserve original window and door placement, "
    "preserve room proportions and geometry, same camera position and perspective, real-world furniture proportions, "
    "commercially available furniture, balanced furniture density, shot on a real camera, 28–35mm lens, interior photography, "
    "architectural digest style, natural color grading, true-to-life colors, realistic materials and textures, "
    "subtle surface imperfections, structural consistency, strict structural preservation"
)

GLOBAL_NEGATIVE_PROMPT = (
    "extra windows, new windows, moved windows, additional doors, new doorways, arches, archways, portals, "
    "hallway creation, room expansion, merged rooms, altered architecture, distorted geometry, unrealistic proportions, "
    "fisheye, ultra wide, extreme perspective, oversaturated colors, CGI look, 3D render look, clutter, messy composition"
)

# Справочник доступных стилей генерации (интерьерная тематика)
# id используется в API и генерации, name/description идут в выдачу /styles
STYLE_CATALOG: List[Dict[str, object]] = [
    {
        "id": "soft-minimal",
        "name": "Софт-минимализм",
        "description": "Светлый минимализм с мягкими формами и спокойным светом",
        "base_prompt": f"{GLOBAL_BASE_PROMPT}. soft minimal interior design, ultra light palette, creamy whites, rounded furniture, soft upholstery, minimal decor, diffused daylight, airy calm atmosphere",
        "negative_prompt": GLOBAL_NEGATIVE_PROMPT,
        "variants": {
            "furniture": [
                "rounded modular sofa, low oak coffee table, soft boucle lounge chair",
                "slim metal console, light fabric sofa, sculptural side table",
                "low-profile sectional, minimal shelves, plush area rug"
            ],
            "walls": [
                "warm white limewash walls, smooth matte finish",
                "very light beige plaster texture",
                "soft off-white paint with subtle sheen"
            ],
            "lighting": [
                "diffused north-facing daylight, soft shadows",
                "hidden cove lighting with warm temperature",
                "neutral ceiling spots with dimmed output"
            ],
            "camera": [
                "35mm calm frontal shot",
                "32mm slight angle for depth",
                "30mm centered symmetrical framing"
            ],
        },
    },
    {
        "id": "warm-modern",
        "name": "Тёплый модерн",
        "description": "Тёплый современный стиль с ощущением уюта и баланса",
        "base_prompt": f"{GLOBAL_BASE_PROMPT}. warm modern interior, warm beige and caramel tones, natural wood and stone, tactile fabrics, elegant modern furniture, soft warm lighting, cozy calm mood",
        "negative_prompt": GLOBAL_NEGATIVE_PROMPT,
        "variants": {
            "furniture": [
                "fabric sofa in warm beige, walnut coffee table, woven pouf",
                "caramel-toned armchairs, travertine side table, soft rug",
                "modern wood console, linen sofa, bronze floor lamp"
            ],
            "walls": [
                "warm beige paint, soft matte",
                "light sand-toned plaster",
                "neutral wall with thin wood slats accent"
            ],
            "lighting": [
                "warm indirect ceiling wash",
                "table lamps with fabric shades, low intensity",
                "window daylight with light curtains, gentle shadows"
            ],
            "camera": [
                "35mm eye-level interior shot",
                "32mm angle capturing seating group",
                "30mm centered view with balanced composition"
            ],
        },
    },
    {
        "id": "neo-japandi",
        "name": "Нео-Япанди",
        "description": "Современный Japandi с дисциплиной и дзен-балансом",
        "base_prompt": f"{GLOBAL_BASE_PROMPT}. neo japandi interior, japanese minimalism with scandinavian precision, low profile furniture, matte wood, stone textures, controlled warm lighting, disciplined composition",
        "negative_prompt": GLOBAL_NEGATIVE_PROMPT,
        "variants": {
            "furniture": [
                "low oak platform sofa, linen cushions, shoji-inspired cabinet",
                "ash wood bench, stone side table, paper lamp",
                "minimal tatami-inspired rug, low coffee table, woven pouf"
            ],
            "walls": [
                "soft greige plaster with subtle texture",
                "light oak panel accent, matte finish",
                "neutral off-white walls, calm tone"
            ],
            "lighting": [
                "controlled warm directional sconces",
                "soft window daylight filtered by linen curtains",
                "hidden floor washer lights, low level"
            ],
            "camera": [
                "32mm calm angle showing depth",
                "35mm straight-on disciplined framing",
                "30mm slight diagonal with leading lines"
            ],
        },
    },
    {
        "id": "organic-modern",
        "name": "Органичный модерн",
        "description": "Природные формы и биоморфный современный дизайн",
        "base_prompt": f"{GLOBAL_BASE_PROMPT}. organic modern interior, sculptural furniture, soft curves, natural stone and wood, earthy tones, organic flow, soft shadows, calm premium atmosphere",
        "negative_prompt": GLOBAL_NEGATIVE_PROMPT,
        "variants": {
                "furniture": [
                "sculptural boucle sofa, pebble coffee table, curved sideboard",
                "organic wood dining table with rounded edges, soft leather chairs",
                "stone pedestal side table, curved lounge chair, wool rug"
            ],
            "walls": [
                "warm clay-toned plaster with soft variation",
                "light taupe microcement, matte",
                "pale sand paint with subtle movement"
            ],
            "lighting": [
                "soft bounced light from wall washers",
                "warm dimmable pendants with frosted glass",
                "natural daylight with sheer curtains, gentle falloff"
            ],
            "camera": [
                "32mm angle highlighting curves",
                "35mm balanced composition, eye level",
                "30mm slight corner view for flow"
            ],
        },
    },
    {
        "id": "wabi-sabi-modern",
        "name": "Ваби-саби модерн",
        "description": "Современный wabi-sabi с фактурой и глубиной",
        "base_prompt": f"{GLOBAL_BASE_PROMPT}. wabi sabi modern interior, textured plaster walls, imperfect surfaces, muted earth tones, aged wood, poetic minimalism, moody natural light",
        "negative_prompt": GLOBAL_NEGATIVE_PROMPT,
        "variants": {
            "furniture": [
                "aged wood bench, linen cushions, ceramic decor",
                "low sofa in muted linen, rough-hewn coffee table",
                "stone stool, vintage sideboard, woven rug"
            ],
            "walls": [
                "hand-troweled clay plaster, visible texture",
                "warm greige limewash with patina",
                "soft earth-toned paint with variation"
            ],
            "lighting": [
                "moody side light, natural shadows",
                "paper lantern diffused glow",
                "narrow beam spot highlighting texture"
            ],
            "camera": [
                "35mm intimate eye-level view",
                "32mm diagonal showing texture depth",
                "30mm calm centered frame"
            ],
        },
    },
    {
        "id": "neo-scandinavian",
        "name": "Нео-скандинавский",
        "description": "Чистый и мягкий скандинавский стиль нового поколения",
        "base_prompt": f"{GLOBAL_BASE_PROMPT}. neo scandinavian interior, light oak wood, soft gray and white palette, functional furniture, clean geometry, abundant natural daylight",
        "negative_prompt": GLOBAL_NEGATIVE_PROMPT,
        "variants": {
            "furniture": [
                "light oak dining table, soft fabric chairs, minimal sideboard",
                "gray fabric sofa, pale wood coffee table, simple shelves",
                "linen curtains, pastel cushions, oak console"
            ],
            "walls": [
                "bright white matte walls",
                "very light gray paint, smooth",
                "white walls with subtle oak trim detail"
            ],
            "lighting": [
                "abundant daylight through sheer curtains",
                "neutral ceiling spots, low intensity",
                "floor lamp with soft white shade"
            ],
            "camera": [
                "35mm airy front view",
                "32mm corner angle to show depth",
                "30mm centered composition, calm"
            ],
        },
    },
    {
        "id": "monochrome-premium",
        "name": "Премиальный монохром",
        "description": "Премиальный монохром с архитектурным светом",
        "base_prompt": f"{GLOBAL_BASE_PROMPT}. monochrome premium interior, grayscale palette, tonal design, luxury materials, deep shadows, soft highlights, cinematic lighting, minimalist composition",
        "negative_prompt": GLOBAL_NEGATIVE_PROMPT,
        "variants": {
            "furniture": [
                "charcoal sofa, black stone coffee table, chrome accents",
                "gray velvet lounge chair, smoked glass side table",
                "graphite cabinetry, minimal shelving, metal floor lamp"
            ],
            "walls": [
                "soft gray paint, low sheen",
                "dark charcoal accent wall, matte",
                "microcement gray wall with fine texture"
            ],
            "lighting": [
                "architectural grazing light, strong contrast",
                "soft box-like ceiling wash, neutral temperature",
                "accent spots highlighting art, dimmed"
            ],
            "camera": [
                "35mm cinematic framing",
                "32mm moody angled shot",
                "30mm centered high-contrast view"
            ],
        },
    },
    {
        "id": "soft-brutalism",
        "name": "Софт-брутализм",
        "description": "Архитектурный брутализм с мягкой подачей",
        "base_prompt": f"{GLOBAL_BASE_PROMPT}. soft brutalism interior, exposed concrete textures, solid architectural forms, minimal furniture with softened edges, neutral gray and warm stone tones, calm architectural atmosphere, soft diffused lighting",
        "negative_prompt": GLOBAL_NEGATIVE_PROMPT,
        "variants": {
            "furniture": [
                "blocky sofa with rounded edges, concrete coffee table",
                "leather lounge chair, stone side table, minimal shelving",
                "low platform seating, metal accents, wool rug"
            ],
            "walls": [
                "light concrete texture, subtle formwork lines",
                "smooth gray plaster with mineral look",
                "concrete finish with warm undertone"
            ],
            "lighting": [
                "soft diffused wall washing",
                "linear ceiling light with neutral tone",
                "daylight with mild shadow, no harsh contrast"
            ],
            "camera": [
                "35mm architectural view",
                "32mm angle emphasizing massing",
                "30mm frontal shot, controlled perspective"
            ],
        },
    },
    {
        "id": "modern-mediterranean",
        "name": "Современный средиземноморский",
        "description": "Современный средиземноморский стиль с солнечным настроением",
        "base_prompt": f"{GLOBAL_BASE_PROMPT}. modern mediterranean interior, limewashed walls, sandy tones, natural stone, linen textiles, sunlit atmosphere, warm southern mood",
        "negative_prompt": GLOBAL_NEGATIVE_PROMPT,
        "variants": {
            "furniture": [
                "linen slipcover sofa, rustic wood coffee table, woven baskets",
                "light wood dining set, ceramic vases, jute rug",
                "rattan chair, stone side table, linen cushions"
            ],
            "walls": [
                "white limewash with gentle variation",
                "soft sand-colored plaster",
                "pale beige stucco, matte"
            ],
            "lighting": [
                "warm coastal daylight, soft shadows",
                "sheer curtains diffusing sun, golden tone",
                "neutral recessed lights, low output"
            ],
            "camera": [
                "35mm bright frontal view",
                "32mm relaxed corner angle",
                "30mm centered sunny composition"
            ],
        },
    },
    {
        "id": "design-hotel",
        "name": "Дизайн-отель",
        "description": "Интерьер как в дизайнерском бутик-отеле",
        "base_prompt": f"{GLOBAL_BASE_PROMPT}. design hotel interior, curated furniture, statement lighting, refined materials, neutral palette with accents, elegant hotel-like composition",
        "negative_prompt": GLOBAL_NEGATIVE_PROMPT,
        "variants": {
            "furniture": [
                "curated lounge chairs, marble coffee table, designer sofa",
                "velvet seating, brass side tables, custom millwork",
                "sculptural accent chair, stone console, layered textiles"
            ],
            "walls": [
                "panelized wall with fabric insert, neutral tone",
                "smooth taupe paint with art pieces",
                "dark accent wall with integrated light strip"
            ],
            "lighting": [
                "statement pendant, warm dim light",
                "wall washers with soft highlights",
                "table lamps with frosted glass, cozy glow"
            ],
            "camera": [
                "35mm hotel lobby-style framing",
                "32mm angle showcasing seating cluster",
                "30mm centered boutique atmosphere"
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
    lighting = _pick_variant(style, "lighting")
    camera = _pick_variant(style, "camera")

    variant_parts = [
        furniture,
        walls,
        lighting,
        camera,
    ]
    variant_text = ", ".join(part for part in variant_parts if part)

    base_prompt = style.get("base_prompt") or ""
    negative_prompt = style.get("negative_prompt") or ""

    positive_parts = []
    if room_type:
        positive_parts.append(
            f"this image shows a {room_type}, keep only appropriate furniture for this {room_type}, no unrelated furniture"
        )
    positive_parts.append(base_prompt)
    if variant_text:
        positive_parts.append(variant_text)

    positive_prompt = ". ".join(part for part in positive_parts if part)

    full_negative = negative_prompt
    if room_negative:
        full_negative = f"{negative_prompt}, {room_negative}" if negative_prompt else room_negative

    meta = {
        "style_id": style_id,
        "base_prompt": str(base_prompt),
        "furniture": furniture,
        "walls": walls,
        "lighting": lighting,
        "camera": camera,
        "negative_prompt": str(full_negative) if full_negative else None,
        "room_type": room_type,
    }
    return positive_prompt, full_negative, meta