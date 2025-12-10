import re
import uuid
import io
from datetime import datetime
from typing import List, Optional
import traceback

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.upload import Upload
from app.models.user import User
from app.services.s3 import (
    create_presigned_url_upload,
    delete_file_by_url,
    get_file_url,
    upload_fileobj_to_s3,
)

router = APIRouter(prefix="/upload", tags=["upload"])


def normalize_filename(filename: str) -> str:
    """
    Normalize filename: replace spaces with underscores, remove special characters.
    Keeps only: letters, numbers, dots, dashes, underscores.
    """
    # Replace spaces with underscores
    normalized = filename.replace(' ', '_')
    # Remove any characters that are not: letters, numbers, dots, dashes, underscores
    normalized = re.sub(r'[^a-zA-Z0-9._-]', '', normalized)
    return normalized


class PresignedUrlRequest(BaseModel):
    filename: str = Field(..., description="Name of the file to upload (spaces will be replaced with underscores)")
    content_type: str = Field(..., description="MIME type of the file (MUST match Content-Type header when uploading)")
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Filename cannot be empty")
        # Normalize filename: replace spaces with underscores
        normalized = normalize_filename(v)
        if not normalized:
            raise ValueError("Filename must contain at least one valid character")
        return normalized
    
    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Content-Type is required and cannot be empty")
        return v.strip()


class PresignedUrlResponse(BaseModel):
    upload_url: str = Field(..., description="Presigned URL for uploading")
    file_url: str = Field(..., description="Public or presigned URL for accessing the file")
    filename: str = Field(..., description="Normalized filename (use this exact name when uploading)")
    content_type: str = Field(..., description="Content-Type to use in upload request (MUST match exactly)")


class UploadResponse(BaseModel):
    file_url: str = Field(..., description="Public URL for accessing the uploaded file")
    filename: str = Field(..., description="Filename in S3")
    fileId: str = Field(..., description="File ID (same as filename)")
    upload_id: int = Field(..., description="ID записи аплоада в базе")
    before: str = Field(..., description="Ссылка на исходную картинку")
    after: Optional[str] = Field(None, description="Ссылка на сгенерированную картинку, если есть")
    style: Optional[str] = Field(None, description="Стиль, примененный при генерации")

    class Config:
        populate_by_name = True


class UploadRecord(BaseModel):
    id: int
    before: str = Field(..., alias="before_url")
    after: Optional[str] = Field(None, alias="after_url")
    style: Optional[str]
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


@router.post("/presign", response_model=PresignedUrlResponse)
def create_presigned_url(
    request: PresignedUrlRequest,
    current_user: User = Depends(get_current_user),
) -> PresignedUrlResponse:
    """
    Create a presigned URL for uploading an image to S3.
    
    Requires authentication.
    
    IMPORTANT: 
    - The filename will be normalized (spaces replaced with underscores)
    - Content-Type MUST match exactly when uploading the file
    - Use the same Content-Type header value as provided in content_type field
    """
    # Filename is already normalized by validator
    # Content-Type is required and validated
    
    # Generate presigned URL for upload
    # Content-Type is always included in signature for security
    upload_url = create_presigned_url_upload(
        request.filename,
        content_type=request.content_type
    )
    
    if not upload_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate presigned upload URL"
        )
    
    # Generate file URL (public or presigned)
    file_url = get_file_url(request.filename)
    
    return PresignedUrlResponse(
        upload_url=upload_url,
        file_url=file_url,
        filename=request.filename,  # Normalized filename
        content_type=request.content_type  # Content-Type to use
    )


@router.post("/create-presigned-url", response_model=PresignedUrlResponse)
def create_presigned_url_alt(
    request: PresignedUrlRequest,
    current_user: User = Depends(get_current_user),
) -> PresignedUrlResponse:
    """
    Alternative endpoint for creating presigned URL (alias for /presign).
    
    Requires authentication.
    """
    return create_presigned_url(request, current_user)


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """
    Upload a file directly to S3 through the backend.
    
    The file is uploaded to S3 and a public URL is returned.
    Filename will be normalized (spaces replaced with underscores).
    
    Requires authentication.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    # Normalize filename
    original_filename = file.filename
    normalized_filename = normalize_filename(original_filename)
    
    # Generate unique filename to avoid conflicts
    # Format: timestamp_uuid_originalname
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    file_extension = ""
    if "." in normalized_filename:
        parts = normalized_filename.rsplit(".", 1)
        if len(parts) == 2:
            normalized_filename = parts[0]
            file_extension = "." + parts[1]
    
    s3_filename = f"{timestamp}_{unique_id}_{normalized_filename}{file_extension}"
    
    # Get content type from file or default to application/octet-stream
    content_type = file.content_type or "application/octet-stream"
    
    # Upload file to S3
    try:
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Create file-like object from bytes
        file_obj = io.BytesIO(file_content)
        
        # Upload to S3
        upload_fileobj_to_s3(
            file_obj,
            s3_filename,
            content_type=content_type
        )
        
        # Generate public URL
        file_url = get_file_url(s3_filename)

        # Сохраняем запись об аплоаде
        upload_record = Upload(
            before_url=file_url,
            created_by=current_user.id,
        )
        db.add(upload_record)
        db.commit()
        db.refresh(upload_record)

        return UploadResponse(
            file_url=file_url,
            filename=s3_filename,
            fileId=s3_filename,
            upload_id=upload_record.id,
            before=upload_record.before_url,
            after=upload_record.after_url,
            style=upload_record.style,
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ClientError as e:
        # Handle S3-specific errors
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        error_trace = traceback.format_exc()
        print(f"S3 ClientError: {error_code} - {error_message}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"S3 upload error: {error_code} - {error_message}"
        )
    except Exception as e:
        # Log full traceback for debugging
        error_trace = traceback.format_exc()
        print(f"Error uploading file: {error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


@router.get("", response_model=List[UploadRecord])
def list_uploads(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[UploadRecord]:
    """
    Получить список аплоадов пользователя (последние сверху).
    """
    uploads = (
        db.query(Upload)
        .filter(Upload.created_by == current_user.id)
        .order_by(Upload.created_at.desc())
        .all()
    )
    return uploads


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_upload(
    upload_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Удалить аплоад и связанные файлы в S3.
    """
    upload = (
        db.query(Upload)
        .filter(
            Upload.id == upload_id,
            Upload.created_by == current_user.id,
        )
        .first()
    )

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found",
        )

    # Чистим S3 (если ссылки валидные)
    for url in [upload.before_url, upload.after_url]:
        if url:
            try:
                delete_file_by_url(url)
            except Exception as e:
                # Не падаем если не удалось удалить, но логируем
                print(f"Failed to delete file {url} from S3: {e}")

    db.delete(upload)
    db.commit()
