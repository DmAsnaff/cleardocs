import os
import logging
from django.conf import settings
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
}
# Map extensions → expected MIME prefix (secondary check when magic unavailable)
_EXT_MIME_MAP = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def validate_upload(file) -> str:
    """
    Validate a Django UploadedFile.
    Returns the detected MIME type on success.
    Raises ValidationError on any violation.
    """
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # 1. Size check
    if file.size > max_bytes:
        raise ValidationError(
            f"File too large. Maximum allowed size is {settings.MAX_UPLOAD_SIZE_MB} MB."
        )

    # 2. Extension check (first line of defence)
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type not supported. Allowed types: PDF, DOCX, JPG, PNG."
        )

    # 3. MIME type via python-magic (reads file header bytes — not the Content-Type header)
    mime_type = _detect_mime(file)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            "File content does not match an allowed document type."
        )

    # 4. Cross-check: extension and content MIME must agree
    expected_mime = _EXT_MIME_MAP.get(ext)
    if expected_mime and mime_type != expected_mime:
        raise ValidationError(
            "File extension and content do not match."
        )

    return mime_type


def _detect_mime(file) -> str:
    """Use python-magic to detect MIME from the first 2 KB of the file."""
    try:
        import magic
        header = file.read(2048)
        file.seek(0)
        return magic.from_buffer(header, mime=True)
    except Exception as exc:
        logger.warning("mime_detection_failed", extra={"error": str(exc)})
        # Fallback: trust the extension mapping
        ext = os.path.splitext(file.name)[1].lower()
        return _EXT_MIME_MAP.get(ext, "application/octet-stream")
