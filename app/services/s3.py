import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import Optional
from urllib.parse import urlparse

from app.core.config import get_settings

settings = get_settings()

# Validate S3 credentials
if not settings.AWS_ACCESS_KEY_ID:
    raise ValueError("AWS_ACCESS_KEY_ID is not set")
if not settings.AWS_SECRET_ACCESS_KEY:
    raise ValueError("AWS_SECRET_ACCESS_KEY is not set")
if not settings.AWS_S3_BUCKET_NAME:
    raise ValueError("AWS_S3_BUCKET_NAME is not set")

# Debug: Check if credentials are read correctly (first few chars only)
print(f"DEBUG S3 Config: Access Key starts with: {settings.AWS_ACCESS_KEY_ID[:10]}...")
print(f"DEBUG S3 Config: Secret Key length: {len(settings.AWS_SECRET_ACCESS_KEY)}")
print(f"DEBUG S3 Config: Secret Key starts with: {settings.AWS_SECRET_ACCESS_KEY[:5]}...")
print(f"DEBUG S3 Config: Secret Key ends with: ...{settings.AWS_SECRET_ACCESS_KEY[-5:]}")
print(f"DEBUG S3 Config: Secret Key contains '+': {'+' in settings.AWS_SECRET_ACCESS_KEY}")
print(f"DEBUG S3 Config: Bucket: {settings.AWS_S3_BUCKET_NAME}")
print(f"DEBUG S3 Config: Region: {settings.AWS_S3_REGION}")

# Configure S3 client to use regional virtual-hosted-style endpoint
# This ensures presigned URLs use regional endpoint (bucket.s3.region.amazonaws.com)
# instead of generic endpoint (bucket.s3.amazonaws.com) to avoid 301 redirects
# Virtual-hosted-style is the standard and preferred addressing style
s3_config = Config(
    region_name=settings.AWS_S3_REGION,
    signature_version='s3v4',
    s3={
        'addressing_style': 'virtual'  # Use virtual-hosted-style (bucket.s3.region.amazonaws.com)
    }
)

client_kwargs = {
    'aws_access_key_id': settings.AWS_ACCESS_KEY_ID.strip(),
    'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY.strip(),
    'region_name': settings.AWS_S3_REGION.strip(),
    'config': s3_config
}

# Only use endpoint_url for custom endpoints (MinIO, DigitalOcean Spaces, etc.)
# For standard S3, boto3 will automatically use regional virtual-hosted-style endpoint
# when region_name is set correctly
if settings.AWS_S3_ENDPOINT_URL:
    client_kwargs['endpoint_url'] = settings.AWS_S3_ENDPOINT_URL.strip()
# Don't set endpoint_url for standard S3 - let boto3 use regional virtual-hosted-style automatically

# Create S3 client for presigned URLs (may use endpoint_url for custom endpoints)
s3_client = boto3.client('s3', **client_kwargs)

# Create separate S3 client for regular operations
# Use the same configuration as s3_client to ensure consistency
# This ensures regular uploads work correctly with AWS S3
s3_client_upload = boto3.client('s3', **client_kwargs)


def create_presigned_url_upload(
    filename: str, 
    expires_in: int = 3600, 
    content_type: Optional[str] = None,
    require_content_type: bool = False
) -> Optional[str]:
    """
    Generate a presigned URL for uploading a file to S3.
    
    The URL will be region-specific (e.g., s3.eu-north-1.amazonaws.com).
    Note: CORS must be configured on the S3 bucket for browser uploads to work.
    
    IMPORTANT: Do not modify the returned URL - it contains a signature that will break if changed.
    
    Args:
        filename: Name of the file to upload (will be URL-encoded automatically)
        expires_in: URL expiration time in seconds (default: 3600)
        content_type: MIME type of the file. If None, ContentType won't be included in signature.
                     If provided, it MUST match exactly the Content-Type header sent by the client.
        require_content_type: If True, content_type must be provided (default: False)
    
    Returns:
        Presigned URL string or None if error occurred
    """
    try:
        if require_content_type and not content_type:
            raise ValueError("content_type is required when require_content_type=True")
        
        # Build parameters for presigned URL
        params = {
            'Bucket': settings.AWS_S3_BUCKET_NAME,
            'Key': filename,  # boto3 will handle URL encoding
        }
        
        # Only include ContentType in signature if provided
        # This makes the signature more flexible but less secure
        if content_type:
            params['ContentType'] = content_type
        
        # Generate presigned URL - boto3 automatically uses the correct regional endpoint
        # based on the region_name specified when creating the client
        # DO NOT modify the returned URL as it will break the signature
        response = s3_client.generate_presigned_url(
            'put_object',
            Params=params,
            ExpiresIn=expires_in
        )
        
        return response
    except (ClientError, ValueError) as e:
        print(f"Error generating presigned upload URL: {e}")
        return None


def create_presigned_url_download(filename: str, expires_in: int = 3600) -> Optional[str]:
    """
    Generate a presigned URL for downloading a file from S3.
    
    Args:
        filename: Name of the file to download
        expires_in: URL expiration time in seconds (default: 3600)
    
    Returns:
        Presigned URL string or None if error occurred
    """
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_S3_BUCKET_NAME,
                'Key': filename
            },
            ExpiresIn=expires_in
        )
        return response
    except ClientError as e:
        print(f"Error generating presigned download URL: {e}")
        return None


def get_file_url(filename: str) -> str:
    """
    Generate a public or presigned URL for accessing a file in S3.
    
    Args:
        filename: Name of the file
    
    Returns:
        URL string (public if bucket is public, otherwise presigned)
    """
    # If bucket is public, return public URL
    # Otherwise, return presigned URL
    if settings.AWS_S3_ENDPOINT_URL:
        # Custom endpoint (e.g., MinIO, DigitalOcean Spaces)
        return f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_S3_BUCKET_NAME}/{filename}"
    else:
        # Standard S3 URL
        return f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{filename}"


def upload_file_to_s3(file_path: str, s3_key: str) -> bool:
    """
    Upload a file to S3 using boto3.
    
    Args:
        file_path: Local path to the file
        s3_key: S3 key (filename) where to store the file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        s3_client.upload_file(file_path, settings.AWS_S3_BUCKET_NAME, s3_key)
        return True
    except ClientError as e:
        print(f"Error uploading file to S3: {e}")
        return False


def upload_fileobj_to_s3(file_obj, s3_key: str, content_type: str = 'image/jpeg') -> bool:
    """
    Upload a file-like object to S3.
    
    Args:
        file_obj: File-like object to upload
        s3_key: S3 key (filename) where to store the file
        content_type: MIME type of the file
    
    Returns:
        True if successful
    
    Raises:
        ClientError: If upload fails
    """
    try:
        # Reset file pointer to beginning if needed
        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)
        
        # Use s3_client_upload for regular operations (without endpoint_url issues)
        # Try using put_object directly for more control
        file_obj.seek(0)
        file_data = file_obj.read()
        
        s3_client_upload.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_data,
            ContentType=content_type
        )
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        print(f"Error uploading file object to S3: {error_code} - {error_message}")
        # Print more details for debugging
        print(f"Bucket: {settings.AWS_S3_BUCKET_NAME}")
        print(f"Key: {s3_key}")
        print(f"Region: {settings.AWS_S3_REGION}")
        print(f"Access Key (first 10): {settings.AWS_ACCESS_KEY_ID[:10]}...")
        raise  # Re-raise to get proper error details


def _extract_key_from_url(url: str) -> Optional[str]:
    """Достать ключ S3 из ссылки вида https://bucket.s3.region.amazonaws.com/key."""
    if not url:
        return None
    parsed = urlparse(url)
    path = parsed.path.lstrip("/")
    if not path:
        return None

    bucket_prefix = f"{settings.AWS_S3_BUCKET_NAME}/"
    if path.startswith(bucket_prefix):
        path = path[len(bucket_prefix):]
    return path or None


def delete_file_from_s3(s3_key: str) -> bool:
    try:
        s3_client_upload.delete_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=s3_key,
        )
        return True
    except ClientError as e:
        print(f"Error deleting file from S3: {e}")
        return False


def delete_file_by_url(url: str) -> bool:
    key = _extract_key_from_url(url)
    if not key:
        print(f"Could not extract S3 key from url: {url}")
        return False
    return delete_file_from_s3(key)

