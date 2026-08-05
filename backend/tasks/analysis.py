"""
AI analysis tasks for the document processing pipeline.

Pipeline shape (inserted after chunk_document):
    chord(
        group(generate_summary, extract_clauses, extract_risks, extract_dates),
        finalise_analysis.s(document_id)
    )

Each parallel task runs an LLM completion and stores partial results on the
DocumentAnalysis record. finalise_analysis merges them and marks the doc DONE.
"""
import json
import logging
from decimal import Decimal
from celery import shared_task
from tasks.pipeline import push_progress, _mark_failed

logger = logging.getLogger(__name__)

# Cost estimate per 1k tokens (gpt-4o-mini / groq is much cheaper — used as ceiling)
_COST_PER_1K_TOKENS = 0.00015


def _get_doc_and_analysis(document_id: str):
    """Fetch Document and get-or-create its DocumentAnalysis record."""
    from apps.documents.models import Document
    from apps.analysis.models import DocumentAnalysis

    doc = Document.objects.get(id=document_id)
    analysis, _ = DocumentAnalysis.objects.get_or_create(
        document=doc,
        defaults={"prompt_version": "v1"},
    )
    return doc, analysis


def _call_llm(system: str, user: str, max_tokens: int = 2048) -> tuple[str, int, str]:
    """Call the configured LLM and return (content, total_tokens, model_name)."""
    from services.llm.factory import get_llm_provider
    provider = get_llm_provider()
    response = provider.complete(system, user, max_tokens=max_tokens)
    return response.content, response.total_tokens, response.model


def _parse_json(raw: str, key: str) -> list | dict:
    """Parse LLM output as JSON; return empty structure on failure."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        logger.warning("llm_json_parse_failed", extra={"key": key, "raw_snippet": raw[:200]})
        return {} if key == "summary" else {key: []}


# ---------------------------------------------------------------------------
# Parallel analysis tasks — each writes one field to DocumentAnalysis
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    name="tasks.analysis.generate_summary",
    queue="llm",
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def generate_summary(self, document_id: str) -> str:
    from services.llm.prompts import summary_system, summary_user
    from services.llm.token_budget import check_user_daily_budget, add_user_tokens

    push_progress(document_id, "analysing", 70, "Generating plain-English summary…")

    doc, analysis = _get_doc_and_analysis(document_id)
    text = doc.extracted_text or ""
    category = doc.doc_category or "general"
    lang = doc.target_language or "en"

    system = summary_system(category, lang)
    user_msg = summary_user(text)

    check_user_daily_budget(str(doc.user_id), 5000)

    try:
        raw, tokens, model = _call_llm(system, user_msg, max_tokens=2048)
        parsed = _parse_json(raw, "summary")

        analysis.summary = parsed.get("summary", "")
        analysis.simplified_text = parsed.get("simplified_text", "")
        analysis.reading_level = parsed.get("reading_level", "")
        analysis.flesch_kincaid_score = parsed.get("flesch_kincaid_score")
        analysis.key_points = parsed.get("key_points", [])
        analysis.word_count = parsed.get("word_count")
        analysis.model_used = model
        analysis.tokens_used = analysis.tokens_used + tokens
        analysis.estimated_cost_usd += Decimal(str(round(tokens / 1000 * _COST_PER_1K_TOKENS, 6)))
        analysis.save(update_fields=[
            "summary", "simplified_text", "reading_level", "flesch_kincaid_score",
            "key_points", "word_count", "model_used", "tokens_used", "estimated_cost_usd",
        ])

        add_user_tokens(str(doc.user_id), tokens)
        logger.info("summary_generated", extra={"document_id": document_id, "tokens": tokens})
    except Exception as exc:
        logger.error("generate_summary_failed", extra={"document_id": document_id, "error": str(exc)})
        raise

    return document_id


@shared_task(
    bind=True,
    name="tasks.analysis.extract_clauses",
    queue="llm",
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def extract_clauses(self, document_id: str) -> str:
    from services.llm.prompts import clauses_system, clauses_user
    from services.llm.token_budget import check_user_daily_budget, add_user_tokens

    push_progress(document_id, "analysing", 72, "Extracting clauses and obligations…")

    doc, analysis = _get_doc_and_analysis(document_id)
    text = doc.extracted_text or ""
    category = doc.doc_category or "general"

    check_user_daily_budget(str(doc.user_id), 5000)

    try:
        raw, tokens, _ = _call_llm(clauses_system(category), clauses_user(text), max_tokens=3000)
        parsed = _parse_json(raw, "clauses")

        analysis.clauses = parsed.get("clauses", [])
        analysis.tokens_used = analysis.tokens_used + tokens
        analysis.estimated_cost_usd += Decimal(str(round(tokens / 1000 * _COST_PER_1K_TOKENS, 6)))
        analysis.save(update_fields=["clauses", "tokens_used", "estimated_cost_usd"])

        add_user_tokens(str(doc.user_id), tokens)
        logger.info("clauses_extracted", extra={"document_id": document_id, "count": len(analysis.clauses)})
    except Exception as exc:
        logger.error("extract_clauses_failed", extra={"document_id": document_id, "error": str(exc)})
        raise

    return document_id


@shared_task(
    bind=True,
    name="tasks.analysis.extract_risks",
    queue="llm",
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def extract_risks(self, document_id: str) -> str:
    from services.llm.prompts import risks_system, risks_user
    from services.llm.token_budget import check_user_daily_budget, add_user_tokens

    push_progress(document_id, "analysing", 74, "Identifying risks and red flags…")

    doc, analysis = _get_doc_and_analysis(document_id)
    text = doc.extracted_text or ""
    category = doc.doc_category or "general"

    check_user_daily_budget(str(doc.user_id), 5000)

    try:
        raw, tokens, _ = _call_llm(risks_system(category), risks_user(text), max_tokens=2048)
        parsed = _parse_json(raw, "risks")

        analysis.risks = parsed.get("risks", [])
        analysis.tokens_used = analysis.tokens_used + tokens
        analysis.estimated_cost_usd += Decimal(str(round(tokens / 1000 * _COST_PER_1K_TOKENS, 6)))
        analysis.save(update_fields=["risks", "tokens_used", "estimated_cost_usd"])

        add_user_tokens(str(doc.user_id), tokens)
        logger.info("risks_extracted", extra={"document_id": document_id, "count": len(analysis.risks)})
    except Exception as exc:
        logger.error("extract_risks_failed", extra={"document_id": document_id, "error": str(exc)})
        raise

    return document_id


@shared_task(
    bind=True,
    name="tasks.analysis.extract_dates",
    queue="llm",
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def extract_dates(self, document_id: str) -> str:
    from services.llm.prompts import dates_system, dates_user
    from services.llm.token_budget import check_user_daily_budget, add_user_tokens

    push_progress(document_id, "analysing", 76, "Extracting important dates and deadlines…")

    doc, analysis = _get_doc_and_analysis(document_id)
    text = doc.extracted_text or ""

    check_user_daily_budget(str(doc.user_id), 5000)

    try:
        raw, tokens, _ = _call_llm(dates_system(), dates_user(text), max_tokens=1024)
        parsed = _parse_json(raw, "key_dates")

        analysis.key_dates = parsed.get("key_dates", [])
        analysis.tokens_used = analysis.tokens_used + tokens
        analysis.estimated_cost_usd += Decimal(str(round(tokens / 1000 * _COST_PER_1K_TOKENS, 6)))
        analysis.save(update_fields=["key_dates", "tokens_used", "estimated_cost_usd"])

        add_user_tokens(str(doc.user_id), tokens)
        logger.info("dates_extracted", extra={"document_id": document_id, "count": len(analysis.key_dates)})
    except Exception as exc:
        logger.error("extract_dates_failed", extra={"document_id": document_id, "error": str(exc)})
        raise

    return document_id


@shared_task(
    bind=True,
    name="tasks.analysis.generate_embeddings",
    queue="llm",
    max_retries=2,
    default_retry_delay=60,
)
def generate_embeddings(self, document_id: str) -> str:
    """Compute and store embeddings for all DocumentChunks."""
    from apps.documents.models import Document, DocumentChunk
    from services.llm.factory import get_llm_provider

    provider = get_llm_provider()

    try:
        doc = Document.objects.get(id=document_id)
        chunks = DocumentChunk.objects.filter(document=doc, embedding__isnull=True)

        updated = []
        for chunk in chunks:
            try:
                chunk.embedding = provider.embed(chunk.text[:8000])
                updated.append(chunk)
            except Exception as exc:
                logger.warning(
                    "embed_chunk_failed",
                    extra={"chunk_id": str(chunk.id), "error": str(exc)},
                )

        if updated:
            DocumentChunk.objects.bulk_update(updated, ["embedding"])

        logger.info("embeddings_generated", extra={"document_id": document_id, "count": len(updated)})
    except Exception as exc:
        logger.error("generate_embeddings_failed", extra={"document_id": document_id, "error": str(exc)})
        # Non-fatal — don't fail the whole document if embeddings fail
    return document_id


# ---------------------------------------------------------------------------
# Chord callback — runs after all parallel tasks complete
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    name="tasks.analysis.finalise_analysis",
    queue="llm",
    max_retries=2,
    default_retry_delay=30,
)
def finalise_analysis(self, results: list, document_id: str) -> str:
    """
    Chord callback. Receives the list of results from the parallel group.
    Verifies the analysis record is populated, transitions document to DONE.
    """
    from apps.documents.models import Document
    from apps.analysis.models import DocumentAnalysis

    push_progress(document_id, "analysing", 90, "Finalising analysis…")

    try:
        doc = Document.objects.get(id=document_id)

        try:
            analysis = DocumentAnalysis.objects.get(document=doc)
        except DocumentAnalysis.DoesNotExist:
            _mark_failed(document_id, "Analysis record missing after parallel tasks.")
            return document_id

        logger.info(
            "analysis_finalised",
            extra={
                "document_id": document_id,
                "tokens_used": analysis.tokens_used,
                "cost_usd": str(analysis.estimated_cost_usd),
                "clauses": len(analysis.clauses),
                "risks": len(analysis.risks),
            },
        )

        # Transition to DONE here — the chord callback is the reliable
        # completion point. A chord embedded mid-chain does NOT reliably
        # propagate the tasks chained after it (notify_complete was being
        # dropped by Celery's canvas), so the DONE transition must not be
        # deferred to a later chain step.
        if doc.status != Document.Status.DONE:
            doc.transition_to(Document.Status.DONE)
        push_progress(document_id, "done", 100, "Your document is ready.")
        return document_id

    except Exception as exc:
        logger.error("finalise_analysis_failed", extra={"document_id": document_id, "error": str(exc)})
        _mark_failed(document_id, str(exc))
        raise self.retry(exc=exc)
