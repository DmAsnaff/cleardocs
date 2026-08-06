"""
Main document processing pipeline.

Chain:
  validate_and_store
  → extract_text
  → chunk_document
  → chord(
        group(generate_summary, extract_clauses, extract_risks, extract_dates),
        finalise_analysis
    )
  → generate_embeddings
  → notify_complete
"""
import logging
from celery import chain, shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def push_progress(document_id: str, status: str, progress: int, message: str) -> None:
    """Broadcast a progress event to the WebSocket group for this document."""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"document_{document_id}",
            {
                "type": "document_progress",
                "data": {
                    "document_id": document_id,
                    "status": status,
                    "progress": progress,
                    "message": message,
                },
            },
        )
    except Exception as exc:
        logger.warning("ws_push_failed", extra={"error": str(exc), "document_id": document_id})


def process_document(document_id: str) -> None:
    """Kick off the full processing chain for a document."""
    from tasks.ocr import validate_and_store, extract_text, chunk_document
    from tasks.analysis import (
        generate_summary, extract_clauses, extract_risks, extract_dates,
        generate_embeddings, finalise_analysis,
    )
    from tasks.pipeline import notify_complete

    # Analyse SEQUENTIALLY (one LLM call at a time) rather than in a parallel
    # group. Firing all four analysis calls at once instantly exceeds the Groq
    # free-tier limit (12k tokens/minute) on large documents, so some sections
    # would 429 and come back empty. A sequential chain — combined with each
    # task's retry/backoff on 429 — keeps us under the limit so every section
    # populates (large docs just take a little longer).
    pipeline = chain(
        validate_and_store.s(document_id),
        extract_text.s(),
        chunk_document.s(),
        generate_summary.si(document_id),
        extract_clauses.si(document_id),
        extract_risks.si(document_id),
        extract_dates.si(document_id),
        generate_embeddings.si(document_id),
        finalise_analysis.si(document_id),
        notify_complete.si(document_id),
    )
    pipeline.apply_async()


@shared_task(
    bind=True,
    name="tasks.pipeline.notify_complete",
    max_retries=3,
    default_retry_delay=10,
)
def notify_complete(self, document_id: str) -> str:
    """Final task: mark document as done and push completion event."""
    from apps.documents.models import Document

    try:
        doc = Document.objects.get(id=document_id)
        if doc.status != Document.Status.DONE:
            doc.transition_to(Document.Status.DONE)

        push_progress(document_id, "done", 100, "Your document is ready.")
        logger.info("pipeline_complete", extra={"document_id": document_id})
        return document_id

    except Exception as exc:
        logger.error("notify_complete_failed", extra={"error": str(exc), "document_id": document_id})
        _mark_failed(document_id, str(exc))
        raise self.retry(exc=exc)


def _mark_failed(document_id: str, error_message: str) -> None:
    """Best-effort: mark the document as failed and push error event."""
    try:
        from apps.documents.models import Document
        doc = Document.objects.get(id=document_id)
        doc.status = Document.Status.FAILED
        doc.error_message = error_message[:500]
        doc.save(update_fields=["status", "error_message"])
    except Exception:
        pass
    push_progress(document_id, "failed", 0, "Processing failed. Please try again.")
