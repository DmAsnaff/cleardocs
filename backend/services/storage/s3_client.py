import os
import uuid
import logging
from typing import Optional
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


class StorageService:
    """Unified storage interface — local filesystem in dev, S3 in production."""

    def _use_s3(self) -> bool:
        return bool(getattr(settings, "AWS_ACCESS_KEY_ID", ""))

    def _get_s3_client(self):
        import boto3
        kwargs = dict(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=getattr(settings, "AWS_S3_REGION_NAME", "us-east-1"),
        )
        endpoint = getattr(settings, "AWS_S3_ENDPOINT_URL", "")
        if endpoint:
            kwargs["endpoint_url"] = endpoint
        return boto3.client("s3", **kwargs)

    def upload(self, file_bytes: bytes, original_filename: str, content_type: str) -> tuple[str, str]:
        """
        Save file to storage.
        Returns (key, bucket) — key is the path; bucket is 'local' for filesystem.
        """
        ext = os.path.splitext(original_filename)[1].lower()
        key = f"documents/{uuid.uuid4()}{ext}"

        if self._use_s3():
            s3 = self._get_s3_client()
            s3.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
                ServerSideEncryption="AES256",
            )
            logger.info("s3_upload", extra={"key": key, "size": len(file_bytes)})
            return key, settings.AWS_STORAGE_BUCKET_NAME

        # Local filesystem
        default_storage.save(key, ContentFile(file_bytes))
        logger.info("local_upload", extra={"key": key, "size": len(file_bytes)})
        return key, "local"

    def get_signed_url(self, key: str, bucket: str, expiry: Optional[int] = None) -> str:
        """Return a URL valid for `expiry` seconds (default from settings)."""
        expiry = expiry or getattr(settings, "AWS_QUERYSTRING_EXPIRE", 900)

        if bucket == "local":
            return f"{settings.MEDIA_URL}{key}"

        s3 = self._get_s3_client()
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expiry,
        )

    def download(self, key: str, bucket: str) -> bytes:
        """Download file bytes from storage."""
        if bucket == "local":
            with default_storage.open(key, "rb") as f:
                return f.read()

        s3 = self._get_s3_client()
        response = s3.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    def delete(self, key: str, bucket: str) -> None:
        """Delete a file from storage."""
        if bucket == "local":
            if default_storage.exists(key):
                default_storage.delete(key)
            return

        s3 = self._get_s3_client()
        s3.delete_object(Bucket=bucket, Key=key)
        logger.info("s3_delete", extra={"key": key})


storage_service = StorageService()
