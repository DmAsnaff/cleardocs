from rest_framework import serializers
from .models import Translation


class TranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Translation
        fields = (
            "id", "language", "summary", "simplified_text",
            "key_points", "clauses", "risks",
            "status", "error_message", "tokens_used",
            "created_at", "updated_at",
        )
        read_only_fields = fields


class TranslationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Translation
        fields = ("id", "language", "status", "error_message", "updated_at")
        read_only_fields = fields


class TranslationRequestSerializer(serializers.Serializer):
    language = serializers.CharField(max_length=10)

    def validate_language(self, value: str) -> str:
        value = value.lower().strip()
        if not value.isalpha() or len(value) > 5:
            raise serializers.ValidationError("Invalid language code.")
        return value
