from typing import Dict, List

# Справочник доступных стилей генерации (интерьерная тематика)
# id используется в API и генерации, name/description идут в выдачу /styles
STYLE_CATALOG: List[Dict[str, str]] = [
    {
        "id": "modern",
        "name": "Современный",
        "description": "Чистые линии, нейтральные оттенки, акценты подсветки",
        "prompt": "modern interior, clean lines, neutral palette, soft indirect lighting, photorealistic render",
    },
    {
        "id": "scandi",
        "name": "Скандинавский",
        "description": "Светлое дерево, белые стены, уютный минимализм",
        "prompt": "scandinavian interior, light wood, white walls, cozy minimal decor, natural light, photorealistic render",
    },
    {
        "id": "loft",
        "name": "Лофт",
        "description": "Бетон, кирпич, металл и открытые коммуникации",
        "prompt": "industrial loft interior, exposed brick, concrete textures, metal accents, high ceiling, photorealistic render",
    },
    {
        "id": "minimalist",
        "name": "Минимализм",
        "description": "Минимум декора и максимум воздуха",
        "prompt": "minimalist interior, decluttered space, large windows, monochrome palette, clean furniture, photorealistic render",
    },
    {
        "id": "classic",
        "name": "Классический",
        "description": "Молдинги, симметрия и благородные материалы",
        "prompt": "classic interior, wall mouldings, symmetry, marble and wood, elegant furniture, photorealistic render",
    },
    {
        "id": "japandi",
        "name": "Япанди",
        "description": "Японский минимализм + скандинавский уют",
        "prompt": "japandi interior, natural textures, low furniture, calm earthy tones, soft lighting, photorealistic render",
    },
    {
        "id": "luxury-modern",
        "name": "Современная роскошь",
        "description": "Премиальные материалы, латунь и подсветка",
        "prompt": "luxury modern interior, marble surfaces, brass accents, ambient lighting, statement furniture, photorealistic render",
    },
    {
        "id": "art-deco",
        "name": "Ар-деко",
        "description": "Геометрия, насыщенные оттенки и глянец",
        "prompt": "art deco interior, geometric patterns, rich colors, glossy finishes, brass details, photorealistic render",
    },
    {
        "id": "mediterranean",
        "name": "Средиземноморский",
        "description": "Арки, штукатурка и теплые природные тона",
        "prompt": "mediterranean interior, white stucco walls, arches, terracotta tiles, natural fabrics, photorealistic render",
    },
]

# Наборы для валидации и быстрого доступа
STYLE_IDS = {style["id"] for style in STYLE_CATALOG}
STYLE_PROMPT_MAP = {style["id"]: style["prompt"] for style in STYLE_CATALOG}

# Пресет для Stability AI — для интерьерных визуализаций оставляем фотореализм
STYLE_PRESET = "photographic"


def get_public_styles() -> List[Dict[str, str]]:
    """Вернуть список стилей без промптов для отдачи наружу."""
    return [
        {key: style[key] for key in ("id", "name", "description")}
        for style in STYLE_CATALOG
    ]

