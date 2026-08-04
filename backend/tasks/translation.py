"""
Translation task: translates DocumentAnalysis content into a target language.
Creates or updates a Translation record for the given document + language.
"""
import logging
import json
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.translation.translate_document",
    queue="llm",
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def translate_document(self, document_id: str, language: str) -> str:
    from apps.documents.models import Document
    from apps.analysis.models import DocumentAnalysis
    from apps.translations.models import Translation
    from services.llm.factory import get_llm_provider

    try:
        doc = Document.objects.get(id=document_id)
        analysis = DocumentAnalysis.objects.get(document=doc)
    except Document.DoesNotExist:
        logger.error("translate_doc_not_found", extra={"document_id": document_id})
        return document_id
    except DocumentAnalysis.DoesNotExist:
        logger.error("translate_analysis_missing", extra={"document_id": document_id})
        translation = Translation.objects.filter(document_id=document_id, language=language).first()
        if translation:
            translation.status = Translation.Status.FAILED
            translation.error_message = "Analysis not available for this document."
            translation.save(update_fields=["status", "error_message"])
        return document_id

    translation, _ = Translation.objects.get_or_create(
        document_id=document_id,
        language=language,
        defaults={"status": Translation.Status.PENDING},
    )

    if translation.status == Translation.Status.DONE:
        return document_id  # idempotent

    translation.status = Translation.Status.PROCESSING
    translation.save(update_fields=["status"])

    provider = get_llm_provider()
    total_tokens = 0

    try:
        # Translate summary
        summary_result, tokens = _translate_text(
            provider,
            analysis.summary,
            language,
            "summary",
        )
        translation.summary = summary_result
        total_tokens += tokens

        # Translate simplified text
        simplified_result, tokens = _translate_text(
            provider,
            analysis.simplified_text,
            language,
            "simplified document text",
        )
        translation.simplified_text = simplified_result
        total_tokens += tokens

        # Translate key points
        if analysis.key_points:
            kp_raw = json.dumps(analysis.key_points)
            kp_result, tokens = _translate_json_list(provider, kp_raw, language, "key points")
            translation.key_points = kp_result
            total_tokens += tokens

        # Translate clause simplified fields
        if analysis.clauses:
            clauses_out = []
            for clause in analysis.clauses:
                translated_simplified, tokens = _translate_text(
                    provider, clause.get("simplified", ""), language, "clause explanation"
                )
                total_tokens += tokens
                clauses_out.append({
                    "title": clause.get("title", ""),
                    "simplified": translated_simplified,
                    "type": clause.get("type", "general"),
                })
            translation.clauses = clauses_out

        # Translate risk descriptions
        if analysis.risks:
            risks_out = []
            for risk in analysis.risks:
                desc, t1 = _translate_text(
                    provider, risk.get("description", ""), language, "risk description"
                )
                rec, t2 = _translate_text(
                    provider, risk.get("recommendation", ""), language, "recommendation"
                )
                total_tokens += t1 + t2
                risks_out.append({
                    "title": risk.get("title", ""),
                    "description": desc,
                    "severity": risk.get("severity", "low"),
                    "recommendation": rec,
                })
            translation.risks = risks_out

        translation.status = Translation.Status.DONE
        translation.model_used = getattr(provider, "_model", "mock")
        translation.tokens_used = total_tokens
        translation.save(update_fields=[
            "summary", "simplified_text", "key_points", "clauses", "risks",
            "status", "model_used", "tokens_used",
        ])

        logger.info(
            "translation_done",
            extra={"document_id": document_id, "language": language, "tokens": total_tokens},
        )

    except Exception as exc:
        translation.status = Translation.Status.FAILED
        translation.error_message = str(exc)[:500]
        translation.save(update_fields=["status", "error_message"])
        logger.error(
            "translate_document_failed",
            extra={"document_id": document_id, "language": language, "error": str(exc)},
        )
        raise

    return document_id


def _translate_text(provider, text: str, language: str, content_type: str) -> tuple[str, int]:
    if not text.strip():
        return "", 0
    system = (
        f"You are a professional translator. Translate the following {content_type} "
        f"into {language}. Return only the translated text, nothing else."
    )
    response = provider.complete(system, text, max_tokens=2048)
    return response.content.strip(), response.total_tokens


def _translate_json_list(
    provider, json_str: str, language: str, content_type: str
) -> tuple[list, int]:
    system = (
        f"You are a professional translator. Translate each item in this JSON array of "
        f"{content_type} into {language}. Return only a valid JSON array of translated strings, nothing else."
    )
    response = provider.complete(system, json_str, max_tokens=1024)
    try:
        result = json.loads(response.content.strip())
        if isinstance(result, list):
            return result, response.total_tokens
    except (json.JSONDecodeError, ValueError):
        pass
    return [], response.total_tokens
