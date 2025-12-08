import uuid
from datetime import datetime
from typing import Optional
import io

from app.core.database import SessionLocal
from app.models.upload import Upload
from app.workers.celery_app import celery_app
from app.services.ai import generate_image
from app.services.s3 import upload_fileobj_to_s3, get_file_url


def _update_upload_after(upload_id: int, user_id: Optional[int], result_url: str) -> None:
    """Записать ссылку на готовое изображение в Upload после генерации."""
    db = SessionLocal()
    try:
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            print(f"[generate_image_task] Upload {upload_id} not found for update")
            return
        if user_id and upload.created_by != user_id:
            print(f"[generate_image_task] Upload {upload_id} does not belong to user {user_id}")
            return

        upload.after_url = result_url
        db.add(upload)
        db.commit()
        print(f"[generate_image_task] Updated upload {upload_id} with after_url")
    except Exception as exc:
        db.rollback()
        print(f"[generate_image_task] Failed to update upload {upload_id}: {exc}")
    finally:
        db.close()


@celery_app.task(bind=True, name="generate_image_task")
def generate_image_task(self, image_url: str, style: str, upload_id: Optional[int] = None, user_id: Optional[int] = None) -> dict:
    """
    Celery task to generate an image using AI API.
    
    Args:
        image_url: URL of the input image
        style: Style to apply
    
    Returns:
        Dictionary with result_url or error message
    """
    try:
        print(f"Starting image generation task: image_url={image_url}, style={style}")
        
        # Generate image (synchronous call)
        image_bytes = generate_image(image_url, style)
        
        if image_bytes is None:
            raise Exception("Failed to generate image: generate_image returned None")
        
        print(f"Image generated successfully, size: {len(image_bytes)} bytes")
        
        # Generate unique filename for result
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        result_filename = f"generated/{style}/{timestamp}_{unique_id}.webp"
        
        # Upload result to S3
        image_file_obj = io.BytesIO(image_bytes)
        upload_success = upload_fileobj_to_s3(
            image_file_obj,
            result_filename,
            content_type="image/webp"
        )
        
        if not upload_success:
            raise Exception("Failed to upload generated image to S3")
        
        # Get public URL for the result
        result_url = get_file_url(result_filename)

        if upload_id:
            _update_upload_after(upload_id, user_id, result_url)
        
        return {
            "status": "success",
            "result_url": result_url,
            "filename": result_filename
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in generate_image_task: {error_msg}")
        # Update task state with error
        self.update_state(
            state="FAILURE",
            meta={"error": error_msg}
        )
        raise Exception(error_msg) from e

