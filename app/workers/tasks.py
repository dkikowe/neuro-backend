import uuid
from datetime import datetime
from typing import Optional

from app.workers.celery_app import celery_app
from app.services.ai import generate_image
from app.services.s3 import upload_fileobj_to_s3, get_file_url
import io


@celery_app.task(bind=True, name="generate_image_task")
def generate_image_task(self, image_url: str, style: str) -> dict:
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

