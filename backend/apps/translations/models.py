import uuid
from django.db import models


class Translation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="translations",
    )
    language = models.CharField(max_length=10)  # ISO 639-1 code

    # Translated content — mirrors relevant DocumentAnalysis fields
    summary = models.TextField(blank=True, default="")
    simplified_text = models.TextField(blank=True, default="")
    key_points = models.JSONField(default=list)
    clauses = models.JSONField(default=list)   # each item: {title, simplified} in target lang
    risks = models.JSONField(default=list)     # each item: {title, description, recommendation}

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    error_message = models.TextField(null=True, blank=True)
    model_used = models.CharField(max_length=100, blank=True, default="")
    tokens_used = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "translations"
        unique_together = [("document", "language")]
        ordering = ["language"]

    def __str__(self):
        return f"Translation({self.document_id}, {self.language})"
