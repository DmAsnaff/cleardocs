import uuid
from django.db import models
from django.conf import settings


class DocumentAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.OneToOneField(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="analysis",
    )

    # LLM outputs — stored as JSON
    summary = models.TextField(blank=True, default="")
    simplified_text = models.TextField(blank=True, default="")
    reading_level = models.CharField(max_length=50, blank=True, default="")
    flesch_kincaid_score = models.FloatField(null=True, blank=True)
    key_points = models.JSONField(default=list)
    clauses = models.JSONField(default=list)
    risks = models.JSONField(default=list)
    key_dates = models.JSONField(default=list)
    word_count = models.IntegerField(null=True, blank=True)

    # Provenance
    prompt_version = models.CharField(max_length=20, default="v1")
    model_used = models.CharField(max_length=100, blank=True, default="")

    # Cost tracking
    tokens_used = models.IntegerField(default=0)
    estimated_cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "document_analyses"

    def __str__(self):
        return f"Analysis({self.document_id})"
