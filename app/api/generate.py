from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from celery.result import AsyncResult

from app.api.deps import get_current_user
from app.models.user import User
from app.workers.tasks import generate_image_task
from app.workers.celery_app import celery_app

router = APIRouter(prefix="/generate", tags=["generate"])


class GenerateRequest(BaseModel):
    image_url: HttpUrl = Field(..., description="URL of the input image")
    style: str = Field(..., description="Style to apply (e.g., 'anime', 'realistic', 'cartoon')")


class GenerateResponse(BaseModel):
    task_id: str = Field(..., description="Celery task ID for tracking")


class TaskStatusResponse(BaseModel):
    status: str = Field(..., description="Task status: PENDING, STARTED, SUCCESS, FAILURE")
    result_url: Optional[str] = Field(None, description="URL of generated image (if status is SUCCESS)")
    error: Optional[str] = Field(None, description="Error message (if status is FAILURE)")


@router.post("", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
def create_generate_task(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user),
) -> GenerateResponse:
    """
    Create a task for generating an image with AI.
    
    Requires authentication.
    Returns task_id for tracking the generation status.
    """
    if not request.style:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Style is required"
        )
    
    # Queue the task
    task = generate_image_task.delay(str(request.image_url), request.style)
    
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
        if isinstance(result, dict) and "result_url" in result:
            response = TaskStatusResponse(
                status="SUCCESS",
                result_url=result["result_url"]
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

