"""
OCR and chunking tasks for the document processing pipeline.
Each task is idempotent: safe to retry if the worker crashes mid-run.
"""
import logging
from celery import shared_task
from tasks.pipeline import push_progress, _mark_failed

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.ocr.validate_and_store",
    queue="ocr",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def validate_and_store(self, document_id: str) -> str:
    """
    Step 1: Virus-scan the uploaded file and transition to EXTRACTING.
    The file is already in storage — this task performs the ClamAV check.
    """
    from apps.documents.models import Document
    from services.storage.s3_client import storage_service
    from services.storage.antivirus import scan_bytes, VirusFoundError

    push_progress(document_id, "validating", 5, "Scanning file for security threats…")

    try:
        doc = Document.objects.get(id=document_id)

        # Idempotent guard: skip if already past this stage
        if doc.status not in (Document.Status.PENDING, Document.Status.VALIDATING):
            return document_id

        doc.transition_to(Document.Status.VALIDATING)

        file_bytes = storage_service.download(doc.s3_key, doc.s3_bucket)

        try:
            scan_bytes(file_bytes, doc.original_filename)
        except VirusFoundError as exc:
            doc.status = Document.Status.FAILED
            doc.error_message = str(exc)
            doc.save(update_fields=["status", "error_message"])
            push_progress(document_id, "failed", 0, "File rejected: security threat detected.")
            return document_id  # Don't retry on virus detection

        doc.transition_to(Document.Status.EXTRACTING)
        push_progress(document_id, "extracting", 15, "Extracting text from document…")
        return document_id

    except Exception as exc:
        logger.error("validate_and_store_failed", extra={"document_id": document_id, "error": str(exc)})
        _mark_failed(document_id, str(exc))
        raise


@shared_task(
    bind=True,
    name="tasks.ocr.extract_text",
    queue="ocr",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def extract_text(self, document_id: str) -> str:
    """
    Step 2: Extract raw text from the file using pdfplumber / pytesseract / python-docx.
    Saves extracted_text to the Document record.
    """
    from apps.documents.models import Document
    from services.storage.s3_client import storage_service
    from services.ocr.extractor import extract_text as do_extract

    push_progress(document_id, "extracting", 25, "Reading document content…")

    try:
        doc = Document.objects.get(id=document_id)

        # Idempotent: if text already extracted, skip
        if doc.extracted_text:
            doc.transition_to(Document.Status.CHUNKING)
            return document_id

        if doc.status not in (Document.Status.EXTRACTING,):
            return document_id

        file_bytes = storage_service.download(doc.s3_key, doc.s3_bucket)
        text = do_extract(file_bytes, doc.mime_type)

        doc.extracted_text = text
        doc.transition_to(Document.Status.CHUNKING)
        doc.save(update_fields=["extracted_text", "status"])

        push_progress(document_id, "chunking", 45, "Splitting document into sections…")
        logger.info("text_extracted", extra={"document_id": document_id, "chars": len(text)})
        return document_id

    except Exception as exc:
        logger.error("extract_text_failed", extra={"document_id": document_id, "error": str(exc)})
        _mark_failed(document_id, str(exc))
        raise


@shared_task(
    bind=True,
    name="tasks.ocr.chunk_document",
    queue="ocr",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def chunk_document(self, document_id: str) -> str:
    """
    Step 3: Split the extracted text into semantically meaningful chunks.
    Creates DocumentChunk records; ready for LLM analysis in Sprint 4.
    """
    from apps.documents.models import Document, DocumentChunk
    from services.ocr.chunker import chunk_document as do_chunk

    push_progress(document_id, "chunking", 55, "Organising document sections…")

    try:
        doc = Document.objects.get(id=document_id)

        if doc.status not in (Document.Status.CHUNKING,):
            return document_id

        # Idempotent: delete any partial chunks before re-creating
        DocumentChunk.objects.filter(document=doc).delete()

        chunks = do_chunk(doc.extracted_text or "")

        DocumentChunk.objects.bulk_create([
            DocumentChunk(
                document=doc,
                chunk_index=c["index"],
                text=c["text"],
                token_count=c["token_count"],
            )
            for c in chunks
        ])

        doc.transition_to(Document.Status.ANALYSING)
        doc.save(update_fields=["status"])

        push_progress(document_id, "analysing", 65, f"Analysing {len(chunks)} sections with AI…")
        logger.info("chunks_created", extra={"document_id": document_id, "count": len(chunks)})
        return document_id

    except Exception as exc:
        logger.error("chunk_document_failed", extra={"document_id": document_id, "error": str(exc)})
        _mark_failed(document_id, str(exc))
        raise
