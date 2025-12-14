import httpx
import io
from typing import Dict, Optional, Tuple

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.core.styles_catalog import build_style_prompt

settings = get_settings()
client = genai.Client(api_key=settings.AI_KEY)


def generate_image(
    image_url: str,
    style: str,
    prompt: Optional[str] = None,
) -> Tuple[bytes, str, Optional[Dict[str, Optional[str]]]]:
    """
    Generate an image using Gemini based on input image and style.
    
    Args:
        image_url: URL of the input image (optional, can be used for image-to-image)
        style: Style to apply (e.g., "anime", "realistic", "cartoon")
        prompt: Text prompt for generation (optional, will be auto-generated if not provided)
    
    Returns:
        Tuple of (image bytes, mime_type)
    """
    try:
        if not settings.AI_KEY:
            raise ValueError("AI_KEY не настроен в переменных окружения")

        # Формируем prompt если не передан
        style_meta: Optional[Dict[str, Optional[str]]] = None

        style_prompt, style_meta = build_style_prompt(style.lower())

        if not prompt:
            base_prompt = (
                "High quality interior visualization, detailed, professional lighting. "
                "Do not change room layout: keep all walls, windows, doors and openings in their original places; "
                "no new openings or relocated windows/doors. "
                "Do not add or remove furniture or decor; only restyle materials, finishes and lighting."
            )
            if style_prompt:
                prompt = f"{base_prompt} {style_prompt}"
            else:
                prompt = f"{base_prompt} Style: {style}"

        if style_meta:
            print(
                "[generate_image] style_meta",
                {
                    "style_id": style_meta.get("style_id"),
                    "furniture": style_meta.get("furniture"),
                    "walls": style_meta.get("walls"),
                    "lighting": style_meta.get("lighting"),
                    "camera": style_meta.get("camera"),
                },
            )

        # Загружаем исходное изображение
        with httpx.Client() as http_client:
            img_response = http_client.get(image_url, timeout=30.0)
            img_response.raise_for_status()
            image_bytes = img_response.content
            mime_type = img_response.headers.get("content-type", "image/jpeg")

        # Готовим части запроса к Gemini
        parts = [
            prompt,
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ]

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=parts,
        )

        # Забираем первое inline-изображение из ответа
        for part in response.parts:
            if getattr(part, "inline_data", None) is not None:
                inline = part.inline_data
                data = inline.data if hasattr(inline, "data") else None
                if data:
                    return data, inline.mime_type or "image/png", style_meta
                # Если as_image доступен, пробуем его
                if hasattr(part, "as_image"):
                    img = part.as_image()
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    return buf.getvalue(), "image/png", style_meta
        raise Exception("Gemini не вернул изображение")

    except httpx.HTTPError as e:
        error_msg = f"HTTP error generating image: {e}"
        print(error_msg)
        raise Exception(error_msg) from e
    except Exception as e:
        error_msg = f"Error generating image: {e}"
        print(error_msg)
        raise Exception(error_msg) from e

