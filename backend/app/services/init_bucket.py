import structlog

from app.config import settings
from app.services.storage import get_s3_client

logger = structlog.get_logger()


def ensure_bucket_exists() -> None:
    """Create the S3 bucket if it doesn't exist and set CORS policy."""
    client = get_s3_client()
    bucket = settings.s3_bucket_name

    try:
        client.head_bucket(Bucket=bucket)
        logger.info("s3_bucket_exists", bucket=bucket)
    except client.exceptions.ClientError:
        client.create_bucket(Bucket=bucket)
        logger.info("s3_bucket_created", bucket=bucket)

    # Set CORS policy for browser uploads
    cors_config = {
        "CORSRules": [
            {
                "AllowedHeaders": ["*"],
                "AllowedMethods": ["GET", "PUT", "POST"],
                "AllowedOrigins": ["http://localhost:3000"],
                "ExposeHeaders": ["ETag"],
                "MaxAgeSeconds": 3600,
            }
        ]
    }
    client.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors_config)
    logger.info("s3_cors_configured", bucket=bucket)
