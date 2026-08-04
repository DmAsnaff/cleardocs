from rest_framework import serializers
from .models import DocumentAnalysis


class DocumentAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnalysis
        fields = (
            "id",
            "summary",
            "simplified_text",
            "reading_level",
            "flesch_kincaid_score",
            "key_points",
            "clauses",
            "risks",
            "key_dates",
            "word_count",
            "prompt_version",
            "model_used",
            "tokens_used",
            "estimated_cost_usd",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ClausesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnalysis
        fields = ("id", "clauses")
        read_only_fields = fields


class RisksSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnalysis
        fields = ("id", "risks")
        read_only_fields = fields
