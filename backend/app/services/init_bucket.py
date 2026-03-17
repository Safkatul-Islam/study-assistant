import json

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
    except client.exceptions.ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code in ("404", "NoSuchBucket"):
            client.create_bucket(Bucket=bucket)
            logger.info("s3_bucket_created", bucket=bucket)
        else:
            raise

    _configure_cors(client, bucket)


def _configure_cors(client, bucket: str) -> None:
    """Set CORS policy for browser-based presigned uploads."""
    cors_config = {
        "CORSRules": [
            {
                "AllowedHeaders": ["*"],
                "AllowedMethods": ["GET", "PUT", "POST"],
                "AllowedOrigins": settings.cors_origins,
                "ExposeHeaders": ["ETag"],
                "MaxAgeSeconds": 3600,
            }
        ]
    }
    try:
        client.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors_config)
        logger.info("s3_cors_configured", bucket=bucket)
    except Exception:
        # MinIO doesn't support put_bucket_cors via S3 API in all versions.
        # Presigned URLs work without explicit CORS on MinIO (it allows them by default).
        # For production (R2/S3), CORS should be configured via the provider's dashboard.
        logger.info("s3_cors_skipped", bucket=bucket, reason="not supported by provider")
