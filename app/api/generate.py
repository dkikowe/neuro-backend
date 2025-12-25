from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, HttpUrl
from celery.result import AsyncResult
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.styles_catalog import STYLE_IDS
from app.services.generations import consume_generation
from app.models.upload import Upload
from app.models.user import User
from app.workers.tasks import generate_image_task
from app.workers.celery_app import celery_app

router = APIRouter(prefix="/generate", tags=["generate"])


class GenerateRequest(BaseModel):
    image_url: HttpUrl = Field(..., description="URL of the input image")
    style: str = Field(..., description="Style id, см. /styles")
    upload_id: Optional[int] = Field(
        None,
        description="ID сохраненного аплоада, чтобы записать after-изображение",
    )
    is_hd: bool = Field(False, description="Запросить HD-генерацию (спишет HD-кредит)")


class GenerateResponse(BaseModel):
    task_id: str = Field(..., description="Celery task ID for tracking")


class TaskStatusResponse(BaseModel):
    status: str = Field(..., description="Task status: PENDING, STARTED, SUCCESS, FAILURE")
    result_url: Optional[str] = Field(None, description="URL of generated image (if status is SUCCESS)")
    filename: Optional[str] = Field(None, description="Filename of generated image in storage")
    style_id: Optional[str] = Field(None, description="Style id that was applied")
    style_meta: Optional[dict] = Field(None, description="Selected style variants (furniture/walls/lighting/camera)")
    error: Optional[str] = Field(None, description="Error message (if status is FAILURE)")


@router.post("", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
def create_generate_task(
    request: GenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GenerateResponse:
    """
    Create a task for generating an image with AI.
    
    Requires authentication.
    Returns task_id for tracking the generation status.
    """
    if not request.style:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Стиль обязателен"
        )

    style_id = request.style.lower()
    if style_id not in STYLE_IDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неподдерживаемый стиль. Проверьте список в /styles",
        )

    # Проверка и списание генерации
    try:
        consume_generation(db, current_user, is_hd=request.is_hd)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(exc),
        )

    # Проверяем, что upload принадлежит пользователю (если указан)
    if request.upload_id is not None:
        upload = (
            db.query(Upload)
            .filter(
                Upload.id == request.upload_id,
                Upload.created_by == current_user.id,
            )
            .first()
        )
        if not upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Аплоад не найден",
            )
        upload.style = style_id
        db.add(upload)
        db.commit()

    # Обновляем счетчик генераций пользователя
    current_user.generation_count = (current_user.generation_count or 0) + 1
    db.add(current_user)
    db.commit()

    # Queue the task (пробрасываем upload_id чтобы записать after)
    task = generate_image_task.delay(
        str(request.image_url),
        style_id,
        request.upload_id,
        current_user.id,
        request.is_hd,
    )

    return GenerateResponse(task_id=task.id)


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
) -> TaskStatusResponse:
    """
    Get the status of a generation task.
    
    Requires authentication.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    # Map Celery states to our response format
    if task_result.state == "PENDING":
        response = TaskStatusResponse(status="PENDING")
    elif task_result.state == "STARTED":
        response = TaskStatusResponse(status="STARTED")
    elif task_result.state == "SUCCESS":
        result = task_result.result
        if isinstance(result, dict):
            response = TaskStatusResponse(
                status="SUCCESS",
                result_url=result.get("result_url"),
                filename=result.get("filename"),
                style_id=result.get("style_id"),
                style_meta=result.get("style_meta"),
            )
        else:
            response = TaskStatusResponse(
                status="SUCCESS",
                result_url=str(result) if result else None
            )
    elif task_result.state == "FAILURE":
        error_info = task_result.info
        error_message = str(error_info) if error_info else "Unknown error"
        response = TaskStatusResponse(
            status="FAILURE",
            error=error_message
        )
    else:
        response = TaskStatusResponse(status=task_result.state)
    
    return response

