import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from pgvector.django import VectorField


def _expires_default():
    from datetime import timedelta
    return timezone.now() + timedelta(days=settings.DOCUMENT_EXPIRY_DAYS)


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        VALIDATING = "validating", "Validating"
        EXTRACTING = "extracting", "Extracting"
        CHUNKING = "chunking", "Chunking"
        ANALYSING = "analysing", "Analysing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    class Category(models.TextChoices):
        LEGAL = "legal", "Legal"
        MEDICAL = "medical", "Medical"
        GOVERNMENT = "government", "Government"
        FINANCIAL = "financial", "Financial"
        OTHER = "other", "Other"

    # Valid forward transitions for the state machine
    _VALID_TRANSITIONS = {
        Status.PENDING: {Status.VALIDATING, Status.FAILED},
        Status.VALIDATING: {Status.EXTRACTING, Status.FAILED},
        Status.EXTRACTING: {Status.CHUNKING, Status.FAILED},
        Status.CHUNKING: {Status.ANALYSING, Status.FAILED},
        Status.ANALYSING: {Status.DONE, Status.FAILED},
        Status.DONE: set(),
        Status.FAILED: set(),
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    original_filename = models.CharField(max_length=500)
    s3_key = models.CharField(max_length=1000)
    s3_bucket = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    file_size_bytes = models.BigIntegerField()
    page_count = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING, db_index=True)
    doc_category = models.CharField(max_length=50, choices=Category.choices, null=True, blank=True)
    target_language = models.CharField(max_length=10, default="en")
    extracted_text = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(default=_expires_default)

    class Meta:
        db_table = "documents"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["user", "-uploaded_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.original_filename} [{self.status}]"

    def transition_to(self, new_status: str) -> None:
        """Enforce state machine — raises ValueError on invalid transition."""
        allowed = self._VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {self.status} → {new_status}"
            )
        self.status = new_status
        if new_status == self.Status.DONE:
            self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at"] if self.processed_at else ["status"])


class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.IntegerField()
    text = models.TextField()
    token_count = models.IntegerField(default=0)
    embedding = VectorField(dimensions=1536, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "document_chunks"
        ordering = ["chunk_index"]
        unique_together = [("document", "chunk_index")]
