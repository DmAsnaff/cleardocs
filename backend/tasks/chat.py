"""
Chat task: RAG retrieval + streaming LLM response pushed over WebSocket.

Flow:
  1. Retrieve top-k relevant chunks via cosine similarity
  2. Build system prompt with document context
  3. Stream LLM response token-by-token via channel_layer
  4. Save the full assistant message
"""
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from celery import shared_task

logger = logging.getLogger(__name__)


def _push_chat_event(session_id: str, event_type: str, data: dict) -> None:
    """Push an event to the chat WebSocket group."""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{session_id}",
            {"type": "chat_message", "data": {"event": event_type, **data}},
        )
    except Exception as exc:
        logger.warning("chat_ws_push_failed", extra={"session_id": session_id, "error": str(exc)})


_CHAT_SYSTEM = """You are a helpful document assistant. Answer the user's question
based ONLY on the document excerpts provided below. Be concise and clear.
If the answer is not in the excerpts, say so honestly.
Always cite the excerpt number(s) you drew from (e.g. "According to Excerpt 2…").

Document excerpts:
{context}"""


@shared_task(
    bind=True,
    name="tasks.chat.stream_chat_response",
    queue="llm",
    max_retries=1,
    default_retry_delay=30,
)
def stream_chat_response(self, session_id: str, user_message_id: str) -> str:
    from apps.chat.models import ChatSession, ChatMessage
    from services.rag.retrieval import retrieve_chunks, build_context
    from services.llm.factory import get_llm_provider

    try:
        session = ChatSession.objects.select_related("document").get(id=session_id)
        user_msg = ChatMessage.objects.get(id=user_message_id)
        document_id = str(session.document_id)

        # RAG retrieval
        chunks = retrieve_chunks(document_id, user_msg.content)
        source_ids = [str(c.id) for c in chunks]
        context = build_context(chunks)

        system_prompt = _CHAT_SYSTEM.format(context=context or "No document content available.")

        # Stream LLM response
        provider = get_llm_provider()
        full_content = ""

        _push_chat_event(session_id, "stream_start", {"message_id": None})

        for chunk in provider.stream_complete(system_prompt, user_msg.content, max_tokens=1024):
            full_content += chunk
            _push_chat_event(session_id, "token", {"content": chunk})

        # Save the assistant message
        assistant_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=full_content,
            sources=source_ids,
        )

        _push_chat_event(session_id, "stream_end", {
            "message_id": str(assistant_msg.id),
            "sources": source_ids,
        })

        logger.info(
            "chat_response_streamed",
            extra={
                "session_id": session_id,
                "response_chars": len(full_content),
                "chunks_used": len(chunks),
            },
        )

    except Exception as exc:
        logger.error(
            "stream_chat_response_failed",
            extra={"session_id": session_id, "error": str(exc)},
        )
        _push_chat_event(session_id, "error", {"message": "Failed to generate response."})
        raise

    return session_id
