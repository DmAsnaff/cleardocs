"""
Tests for the chat session, messaging, and RAG retrieval.
LLM calls use MockProvider. Celery tasks run eagerly.
"""
import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.documents.models import Document, DocumentChunk
from apps.chat.models import ChatSession, ChatMessage
from apps.documents.tests.factories import DocumentFactory
from apps.users.tests.factories import UserFactory


def _auth_client(user) -> APIClient:
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


def _sessions_url(doc_id):
    return f"/api/v1/documents/{doc_id}/chat/sessions/"


def _session_url(doc_id, session_id):
    return f"/api/v1/documents/{doc_id}/chat/sessions/{session_id}/"


def _messages_url(doc_id, session_id):
    return f"/api/v1/documents/{doc_id}/chat/sessions/{session_id}/messages/"


def _make_done_doc(user):
    return DocumentFactory(user=user, status=Document.Status.DONE, extracted_text="Contract text.")


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChatSessionCRUD:
    def test_create_session(self):
        user = UserFactory()
        doc = _make_done_doc(user)
        client = _auth_client(user)

        resp = client.post(_sessions_url(doc.id), {}, format="json")
        assert resp.status_code == 201
        assert ChatSession.objects.filter(document=doc, user=user).exists()

    def test_create_session_requires_done_document(self):
        user = UserFactory()
        doc = DocumentFactory(user=user, status=Document.Status.PENDING)
        client = _auth_client(user)

        resp = client.post(_sessions_url(doc.id), {}, format="json")
        assert resp.status_code == 409

    def test_list_sessions(self):
        user = UserFactory()
        doc = _make_done_doc(user)
        ChatSession.objects.create(document=doc, user=user)
        ChatSession.objects.create(document=doc, user=user)
        client = _auth_client(user)

        resp = client.get(_sessions_url(doc.id))
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    def test_get_session_with_messages(self):
        user = UserFactory()
        doc = _make_done_doc(user)
        session = ChatSession.objects.create(document=doc, user=user)
        ChatMessage.objects.create(session=session, role=ChatMessage.Role.USER, content="Hello?")
        client = _auth_client(user)

        resp = client.get(_session_url(doc.id, session.id))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["message_count"] == 1
        assert len(data["messages"]) == 1

    def test_delete_session(self):
        user = UserFactory()
        doc = _make_done_doc(user)
        session = ChatSession.objects.create(document=doc, user=user)
        client = _auth_client(user)

        resp = client.delete(_session_url(doc.id, session.id))
        assert resp.status_code == 200
        assert not ChatSession.objects.filter(id=session.id).exists()

    def test_session_ownership_enforced(self):
        owner = UserFactory()
        attacker = UserFactory()
        doc = _make_done_doc(owner)
        session = ChatSession.objects.create(document=doc, user=owner)
        client = _auth_client(attacker)

        resp = client.get(_session_url(doc.id, session.id))
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Messaging
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChatMessaging:
    @patch("tasks.chat.stream_chat_response.delay")
    def test_send_message_creates_user_message(self, mock_task):
        user = UserFactory()
        doc = _make_done_doc(user)
        session = ChatSession.objects.create(document=doc, user=user)
        client = _auth_client(user)

        resp = client.post(
            _messages_url(doc.id, session.id),
            {"content": "What does clause 3 say?"},
            format="json",
        )
        assert resp.status_code == 202
        assert ChatMessage.objects.filter(session=session, role=ChatMessage.Role.USER).exists()
        mock_task.assert_called_once()

    @patch("tasks.chat.stream_chat_response.delay")
    def test_first_message_auto_titles_session(self, mock_task):
        user = UserFactory()
        doc = _make_done_doc(user)
        session = ChatSession.objects.create(document=doc, user=user, title="")
        client = _auth_client(user)

        client.post(
            _messages_url(doc.id, session.id),
            {"content": "Who are the parties to this contract?"},
            format="json",
        )
        session.refresh_from_db()
        assert session.title == "Who are the parties to this contract?"

    def test_empty_message_rejected(self):
        user = UserFactory()
        doc = _make_done_doc(user)
        session = ChatSession.objects.create(document=doc, user=user)
        client = _auth_client(user)

        resp = client.post(_messages_url(doc.id, session.id), {"content": ""}, format="json")
        assert resp.status_code == 400

    @patch("tasks.chat.stream_chat_response.delay")
    def test_message_too_long_rejected(self, mock_task):
        user = UserFactory()
        doc = _make_done_doc(user)
        session = ChatSession.objects.create(document=doc, user=user)
        client = _auth_client(user)

        resp = client.post(
            _messages_url(doc.id, session.id),
            {"content": "x" * 4001},
            format="json",
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Chat Celery task
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestStreamChatResponseTask:
    @patch("tasks.chat._push_chat_event")
    def test_task_creates_assistant_message(self, mock_push):
        from tasks.chat import stream_chat_response
        user = UserFactory()
        doc = _make_done_doc(user)
        DocumentChunk.objects.create(document=doc, chunk_index=0, text="Payment clause text.", token_count=5)

        session = ChatSession.objects.create(document=doc, user=user)
        user_msg = ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.USER, content="What is the payment term?"
        )

        stream_chat_response(str(session.id), str(user_msg.id))

        assert ChatMessage.objects.filter(session=session, role=ChatMessage.Role.ASSISTANT).exists()

    @patch("tasks.chat._push_chat_event")
    def test_task_pushes_stream_end_event(self, mock_push):
        from tasks.chat import stream_chat_response
        user = UserFactory()
        doc = _make_done_doc(user)
        session = ChatSession.objects.create(document=doc, user=user)
        user_msg = ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.USER, content="Summarise."
        )

        stream_chat_response(str(session.id), str(user_msg.id))

        event_types = [call.args[1] for call in mock_push.call_args_list]
        assert "stream_end" in event_types


# ---------------------------------------------------------------------------
# RAG retrieval
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRAGRetrieval:
    def test_retrieval_returns_chunks_fallback(self):
        from services.rag.retrieval import retrieve_chunks
        user = UserFactory()
        doc = _make_done_doc(user)
        DocumentChunk.objects.create(document=doc, chunk_index=0, text="First chunk.", token_count=5)
        DocumentChunk.objects.create(document=doc, chunk_index=1, text="Second chunk.", token_count=5)

        # No embeddings — falls back to ordered chunks
        chunks = retrieve_chunks(str(doc.id), "What is this about?", top_k=2)
        assert len(chunks) == 2

    def test_build_context_formats_excerpts(self):
        from services.rag.retrieval import build_context
        from apps.documents.models import DocumentChunk
        user = UserFactory()
        doc = _make_done_doc(user)
        c1 = DocumentChunk(document=doc, chunk_index=0, text="Clause one text.", token_count=5)
        c2 = DocumentChunk(document=doc, chunk_index=1, text="Clause two text.", token_count=5)

        ctx = build_context([c1, c2])
        assert "Excerpt 1" in ctx
        assert "Clause one text." in ctx
        assert "Excerpt 2" in ctx
