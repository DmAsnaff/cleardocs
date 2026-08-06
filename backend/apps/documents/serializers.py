from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.SerializerMethodField()
    signed_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id", "original_filename", "mime_type", "file_size_bytes", "file_size_mb",
            "page_count", "status", "doc_category", "target_language",
            "error_message", "uploaded_at", "processed_at", "expires_at",
            "signed_url",
        )
        read_only_fields = fields

    def get_file_size_mb(self, obj) -> str:
        return f"{obj.file_size_bytes / (1024 * 1024):.2f} MB"

    def get_signed_url(self, obj) -> str | None:
        if obj.status != Document.Status.DONE:
            return None
        try:
            from services.storage.s3_client import storage_service
            url = storage_service.get_signed_url(obj.s3_key, obj.s3_bucket)
        except Exception:
            return None
        # Local storage returns a root-relative /media/ path; make it absolute
        # so the frontend (a different origin in dev) can load it.
        request = self.context.get("request")
        if url and request and url.startswith("/"):
            return request.build_absolute_uri(url)
        return url


class DocumentStatusSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the polling status endpoint."""
    class Meta:
        model = Document
        fields = ("id", "status", "error_message", "processed_at")
        read_only_fields = fields


class DocumentUploadSerializer(serializers.Serializer):
    """Validates the incoming multipart upload request."""
    file = serializers.FileField()
    doc_category = serializers.ChoiceField(
        choices=Document.Category.choices,
        required=False,
        default=Document.Category.OTHER,
    )
    target_language = serializers.CharField(max_length=10, required=False, default="en")
