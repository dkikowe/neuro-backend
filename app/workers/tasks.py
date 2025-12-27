import uuid
from datetime import datetime
from typing import Optional, Dict
import io

from app.core.database import SessionLocal
from app.models.upload import Upload
from app.workers.celery_app import celery_app
from app.services.ai import generate_image
from app.services.s3 import upload_fileobj_to_s3, get_file_url
from app.services.upscale import upscale_image_fast
from app.models.style_stat import StyleStat


def _update_upload_after(upload_id: int, user_id: Optional[int], result_url: str, style: Optional[str]) -> None:
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
        if style:
            upload.style = style
        db.add(upload)
        db.commit()
        print(f"[generate_image_task] Updated upload {upload_id} with after_url")
    except Exception as exc:
        db.rollback()
        print(f"[generate_image_task] Failed to update upload {upload_id}: {exc}")
    finally:
        db.close()


def _increment_style_stat(style: Optional[str]) -> None:
    if not style:
        return
    db = SessionLocal()
    try:
        stat = db.query(StyleStat).filter(StyleStat.style_id == style).first()
        if not stat:
            stat = StyleStat(style_id=style, count=1)
            db.add(stat)
        else:
            stat.count = (stat.count or 0) + 1
            db.add(stat)
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"[style_stat] Failed to increment stat for {style}: {exc}")
    finally:
        db.close()


@celery_app.task(bind=True, name="generate_image_task")
def generate_image_task(
    self,
    image_url: str,
    style: str,
    upload_id: Optional[int] = None,
    user_id: Optional[int] = None,
    is_hd: bool = False,
) -> dict:
    """
    Celery task to generate an image using AI API.
    
    Args:
        image_url: URL of the input image
        style: Style to apply
    
    Returns:
        Dictionary with result_url or error message
    """
    try:
        print(f"Starting image generation task: image_url={image_url}, style={style}, is_hd={is_hd}")
        
        # Generate image (synchronous call)
        image_bytes, mime_type, style_meta = generate_image(image_url, style)
        
        if image_bytes is None:
            raise Exception("Failed to generate image: generate_image returned None")
        
        print(f"Image generated successfully, size: {len(image_bytes)} bytes")

        # HD upscale if requested
        if is_hd:
            try:
                image_bytes, mime_type = upscale_image_fast(image_bytes, output_format="webp")
                print(f"HD upscale done, size: {len(image_bytes)} bytes, mime: {mime_type}")
            except Exception as exc:
                raise Exception(f"Не удалось выполнить HD-генерацию: {exc}")
        
        # Generate unique filename for result
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        ext_map = {
            "image/png": "png",
            "image/jpeg": "jpg",
            "image/webp": "webp",
        }
        ext = ext_map.get(mime_type.lower(), "png")
        result_filename = f"generated/{style}/{timestamp}_{unique_id}.{ext}"
        
        # Upload result to S3
        image_file_obj = io.BytesIO(image_bytes)
        print(f"Uploading to S3: key={result_filename}, mime={mime_type}, bytes={len(image_bytes)}")
        upload_success = upload_fileobj_to_s3(
            image_file_obj,
            result_filename,
            content_type=mime_type
        )
        
        if not upload_success:
            raise Exception("Failed to upload generated image to S3")
        
        print(f"Uploaded to S3 successfully: key={result_filename}")

        # Get public URL for the result
        result_url = get_file_url(result_filename)

        if upload_id:
            _update_upload_after(upload_id, user_id, result_url, style)
        _increment_style_stat(style)
        
        return {
            "status": "success",
            "result_url": result_url,
            "filename": result_filename,
            "style_id": style,
            "style_meta": style_meta,
            "is_hd": is_hd,
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in generate_image_task: {error_msg}")
        raise Exception(error_msg) from e

