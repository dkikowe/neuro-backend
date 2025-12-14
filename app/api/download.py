from fastapi import APIRouter, HTTPException, Query, status, Response

from app.services.s3 import download_file_from_s3
from app.services.upscale import upscale_image_fast

router = APIRouter(prefix="/api", tags=["download"])


@router.get("/download")
def download_file(
    key: str = Query(..., description="S3 key файла"),
    hd: bool = Query(False, description="Если true — апскейл перед скачиванием"),
) -> Response:
    """
    Скачать сгенерированную картинку из S3 по ключу.

    Отдаёт как attachment с filename из ключа.
    """
    if not key or key.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Параметр key обязателен",
        )

    file_bytes, content_type = download_file_from_s3(key)
    if file_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден",
        )

    # Опциональный апскейл при скачивании
    if hd:
        fmt = "webp" if (content_type and "webp" in content_type.lower()) else "png"
        upscaled_bytes, upscaled_type = upscale_image_fast(file_bytes, output_format=fmt)
        if upscaled_bytes:
            file_bytes = upscaled_bytes
            content_type = upscaled_type

    filename = key.split("/")[-1] if "/" in key else key
    return Response(
        content=file_bytes,
        media_type=content_type or "image/png",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )

