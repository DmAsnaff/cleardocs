from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ("id", "role", "content", "sources", "tokens_used", "created_at")
        read_only_fields = fields


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ("id", "document_id", "title", "message_count", "messages", "created_at", "updated_at")
        read_only_fields = fields

    def get_message_count(self, obj) -> int:
        # Use annotation when available (avoids extra query in list context)
        if hasattr(obj, "message_count_annotated"):
            return obj.message_count_annotated
        # Detail view: messages are already fetched — count from cache
        messages = obj.messages.all()
        if messages._result_cache is not None:
            return len(messages)
        return messages.count()


class ChatSessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view — message_count comes from queryset annotation."""
    message_count = serializers.IntegerField(read_only=True)  # annotated as 'message_count'

    class Meta:
        model = ChatSession
        fields = ("id", "document_id", "title", "message_count", "created_at", "updated_at")
        read_only_fields = fields


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=4000, trim_whitespace=True)
