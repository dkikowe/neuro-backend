import httpx
import io
from typing import Optional

from app.core.config import get_settings

settings = get_settings()

# Маппинг стилей на style_preset Stability AI
STYLE_PRESET_MAP = {
    "anime": "anime",
    "realistic": "photographic",
    "cartoon": "comic-book",
    "digital-art": "digital-art",
    "fantasy": "fantasy-art",
    "cinematic": "cinematic",
    "3d": "3d-model",
    "pixel": "pixel-art",
    "neon": "neon-punk",
    "isometric": "isometric",
    "low-poly": "low-poly",
    "line-art": "line-art",
    "origami": "origami",
    "tile": "tile-texture",
    "modeling": "modeling-compound",
    "analog": "analog-film",
    "enhance": "enhance",
}


def generate_image(image_url: str, style: str, prompt: Optional[str] = None) -> Optional[bytes]:
    """
    Generate an image using Stability AI API based on input image and style.
    
    Args:
        image_url: URL of the input image (optional, can be used for image-to-image)
        style: Style to apply (e.g., "anime", "realistic", "cartoon")
        prompt: Text prompt for generation (optional, will be auto-generated if not provided)
    
    Returns:
        Generated image bytes or None if error occurred
    """
    try:
        if not settings.AI_KEY:
            raise ValueError("AI_KEY не настроен в переменных окружения")
        
        # Получаем style_preset из маппинга или используем style как есть
        style_preset = STYLE_PRESET_MAP.get(style.lower(), style.lower())
        
        # Формируем prompt если не передан
        if not prompt:
            prompt = f"High quality image in {style} style, detailed, professional"
        
        # Подготавливаем multipart/form-data для запроса
        # В httpx все поля multipart должны быть в files
        files = {
            "prompt": (None, prompt),
            "output_format": (None, "webp"),
            "style_preset": (None, style_preset),
        }
        
        # Если передан image_url, загружаем изображение и используем для image-to-image
        if image_url:
            with httpx.Client() as client:
                # Загружаем исходное изображение
                img_response = client.get(image_url, timeout=30.0)
                img_response.raise_for_status()
                image_bytes = img_response.content
                
                # Определяем формат изображения
                content_type = img_response.headers.get("content-type", "image/jpeg")
                if "png" in content_type:
                    image_format = "png"
                elif "webp" in content_type:
                    image_format = "webp"
                else:
                    image_format = "jpeg"
                
                # Добавляем изображение в запрос
                files["image"] = (f"image.{image_format}", io.BytesIO(image_bytes), f"image/{image_format}")
                # Добавляем strength для image-to-image (0.7 - среднее значение)
                files["strength"] = (None, "0.7")
        else:
            # Если нет изображения, используем "none" как в документации
            files["none"] = (None, "")
        
        # Отправляем запрос к Stability AI
        with httpx.Client() as client:
            response = client.post(
                "https://api.stability.ai/v2beta/stable-image/generate/ultra",
                headers={
                    "authorization": f"Bearer {settings.AI_KEY}",
                    "accept": "image/*",
                },
                files=files,
                timeout=120.0,  # Увеличиваем таймаут для генерации
            )
            
            if response.status_code == 200:
                return response.content
            else:
                error_msg = f"Stability AI API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data}"
                except:
                    error_msg += f" - {response.text}"
                raise Exception(error_msg)
            
    except httpx.HTTPError as e:
        error_msg = f"HTTP error generating image: {e}"
        print(error_msg)
        raise Exception(error_msg) from e
    except Exception as e:
        error_msg = f"Error generating image: {e}"
        print(error_msg)
        raise Exception(error_msg) from e

