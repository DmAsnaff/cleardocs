"""
RAG retrieval: embed a query, then find the most relevant DocumentChunks
using pgvector cosine similarity.
"""
import logging
from django.db.models import QuerySet

logger = logging.getLogger(__name__)

_DEFAULT_TOP_K = 4


def retrieve_chunks(document_id: str, query: str, top_k: int = _DEFAULT_TOP_K) -> list:
    """
    Embed the query and return the top_k most relevant DocumentChunks.
    Falls back to returning the first top_k chunks in order if pgvector
    or embeddings are unavailable.
    """
    from apps.documents.models import DocumentChunk
    from services.llm.factory import get_llm_provider

    provider = get_llm_provider()

    try:
        query_embedding = provider.embed(query)
        results = _cosine_search(document_id, query_embedding, top_k)
        if results:
            return results
        # No embedded chunks yet — fall through to the ordered fallback.
    except Exception as exc:
        logger.warning(
            "rag_cosine_search_failed",
            extra={"document_id": document_id, "error": str(exc)},
        )

    # Fallback: return first top_k chunks in order.
    return list(
        DocumentChunk.objects.filter(document_id=document_id).order_by("chunk_index")[:top_k]
    )


def _cosine_search(document_id: str, query_embedding: list[float], top_k: int) -> list:
    from pgvector.django import CosineDistance
    from apps.documents.models import DocumentChunk

    return list(
        DocumentChunk.objects.filter(
            document_id=document_id,
            embedding__isnull=False,
        )
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:top_k]
    )


def build_context(chunks: list) -> str:
    """Concatenate chunk texts into a single context string for the LLM prompt."""
    if not chunks:
        return ""
    parts = [f"[Excerpt {i + 1}]\n{chunk.text}" for i, chunk in enumerate(chunks)]
    return "\n\n".join(parts)
