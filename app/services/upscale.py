import httpx
from typing import Tuple

from app.core.config import get_settings

settings = get_settings()


def upscale_image_fast(image_bytes: bytes, output_format: str = "webp") -> Tuple[bytes, str]:
    """
    Upscale image 4x using Stability Fast Upscaler.

    Returns (image_bytes, mime_type). On failure or missing key returns original.
    """
    api_key = settings.STABILITY_AI_KEY
    if not api_key:
        return image_bytes, f"image/{output_format}"

    # Ensure allowed format
    if output_format not in {"png", "jpeg", "webp"}:
        output_format = "png"

    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                "https://api.stability.ai/v2beta/stable-image/upscale/fast",
                headers={
                    "authorization": f"Bearer {api_key}",
                    "accept": "image/*",
                },
                files={
                    "image": ("image", image_bytes, "application/octet-stream"),
                },
                data={
                    "output_format": output_format,
                },
            )

        if resp.status_code == 200:
            mime = resp.headers.get("content-type", f"image/{output_format}")
            return resp.content, mime

        # If API returns JSON error, log minimal info
        try:
            print(f"Upscale error: {resp.status_code} - {resp.json()}")
        except Exception:
            print(f"Upscale error: {resp.status_code} - {resp.text}")
        return image_bytes, f"image/{output_format}"

    except Exception as exc:
        print(f"Upscale exception: {exc}")
        return image_bytes, f"image/{output_format}"


