import boto3
from botocore.config import Config

from app.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4"),
    )


def generate_presigned_upload_url(s3_key: str, content_type: str = "application/pdf") -> str:
    client = get_s3_client()
    return client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket_name,
            "Key": s3_key,
            "ContentType": content_type,
        },
        ExpiresIn=300,  # 5 minutes
    )


def generate_presigned_download_url(s3_key: str) -> str:
    client = get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.s3_bucket_name,
            "Key": s3_key,
        },
        ExpiresIn=3600,  # 1 hour
    )


def download_file_bytes(s3_key: str) -> bytes:
    client = get_s3_client()
    response = client.get_object(Bucket=settings.s3_bucket_name, Key=s3_key)
    return response["Body"].read()


def delete_s3_object(s3_key: str) -> None:
    client = get_s3_client()
    client.delete_object(Bucket=settings.s3_bucket_name, Key=s3_key)
