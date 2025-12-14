from fastapi import APIRouter, HTTPException, Query, status, Response

from app.services.s3 import download_file_from_s3

router = APIRouter(prefix="/api", tags=["download"])


@router.get("/download")
def download_file(key: str = Query(..., description="S3 key файла")) -> Response:
    """
    Скачать сгенерированную картинку из S3 по ключу.

    Отдаёт как attachment с filename из ключа.
    """
    if not key or key.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="key is required",
        )

    file_bytes, content_type = download_file_from_s3(key)
    if file_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    filename = key.split("/")[-1] if "/" in key else key
    return Response(
        content=file_bytes,
        media_type=content_type or "image/png",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )

