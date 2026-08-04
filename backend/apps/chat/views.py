import logging
from django.db.models import Count
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import Document
from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionSerializer, ChatSessionListSerializer,
    ChatMessageSerializer, SendMessageSerializer,
)

logger = logging.getLogger(__name__)


def _success(data=None, message="", status_code=status.HTTP_200_OK):
    return Response({"status": "success", "message": message, "data": data}, status=status_code)


def _error(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({"status": "error", "message": message, "errors": errors or {}}, status=status_code)


def _get_document_or_error(document_id: str, user) -> Document:
    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        raise NotFound("Document not found.")
    if doc.user_id != user.id:
        raise PermissionDenied("You do not have access to this document.")
    return doc


def _get_session_or_error(session_id: str, user) -> ChatSession:
    try:
        session = ChatSession.objects.get(id=session_id)
    except ChatSession.DoesNotExist:
        raise NotFound("Chat session not found.")
    if session.user_id != user.id:
        raise PermissionDenied("You do not have access to this session.")
    return session


class ChatSessionListCreateView(APIView):
    """
    GET  /api/v1/documents/{id}/chat/sessions/  — list sessions for document
    POST /api/v1/documents/{id}/chat/sessions/  — create a new session
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        doc = _get_document_or_error(document_id, request.user)
        sessions = (
            ChatSession.objects
            .filter(document=doc, user=request.user)
            .annotate(message_count=Count("messages"))
        )
        return _success(ChatSessionListSerializer(sessions, many=True).data)

    def post(self, request, document_id):
        doc = _get_document_or_error(document_id, request.user)
        if doc.status != Document.Status.DONE:
            return _error(
                "Document must be processed before starting a chat.",
                status_code=status.HTTP_409_CONFLICT,
            )
        session = ChatSession.objects.create(
            document=doc,
            user=request.user,
            title=request.data.get("title", ""),
        )
        logger.info("chat_session_created", extra={"session_id": str(session.id)})
        return _success(ChatSessionSerializer(session).data, status_code=status.HTTP_201_CREATED)


class ChatSessionDetailView(APIView):
    """
    GET    /api/v1/documents/{id}/chat/sessions/{sid}/  — get session + all messages
    DELETE /api/v1/documents/{id}/chat/sessions/{sid}/  — delete session
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id, session_id):
        _get_document_or_error(document_id, request.user)
        session = _get_session_or_error(session_id, request.user)
        return _success(ChatSessionSerializer(session).data)

    def delete(self, request, document_id, session_id):
        _get_document_or_error(document_id, request.user)
        session = _get_session_or_error(session_id, request.user)
        session.delete()
        return _success(message="Chat session deleted.")


class ChatMessageCreateView(APIView):
    """
    POST /api/v1/documents/{id}/chat/sessions/{sid}/messages/
    Creates the user message, enqueues the streaming response task.
    The actual AI response arrives over the WebSocket.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id, session_id):
        _get_document_or_error(document_id, request.user)
        session = _get_session_or_error(session_id, request.user)

        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return _error("Invalid request.", serializer.errors)

        user_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            content=serializer.validated_data["content"],
        )

        # Auto-title the session from the first user message
        if not session.title and session.messages.count() == 1:
            session.title = serializer.validated_data["content"][:80]
            session.save(update_fields=["title"])

        from tasks.chat import stream_chat_response
        stream_chat_response.delay(str(session.id), str(user_msg.id))

        return _success(
            ChatMessageSerializer(user_msg).data,
            "Message sent. Response streaming via WebSocket.",
            status.HTTP_202_ACCEPTED,
        )
