"""
Scheduled maintenance tasks (run by Celery Beat).

  delete_expired_documents — 2 AM UTC daily
    Deletes documents past their expires_at date from S3 and DB.
    Also cascades to DocumentChunk, DocumentAnalysis, Translation, ChatSession.

  reset_daily_upload_counts — midnight UTC daily
    Resets User.daily_upload_count = 0 for all users whose counter is stale.

  purge_deleted_users — 3 AM UTC daily
    Hard-deletes users soft-deleted more than 30 days ago (GDPR purge).
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="tasks.maintenance.delete_expired_documents")
def delete_expired_documents() -> dict:
    from apps.documents.models import Document
    from services.storage.s3_client import storage_service

    now = timezone.now()
    expired = Document.objects.filter(expires_at__lt=now)
    count = 0
    errors = 0

    for doc in expired.iterator(chunk_size=100):
        try:
            storage_service.delete(doc.s3_key, doc.s3_bucket)
        except Exception as exc:
            logger.warning(
                "expire_storage_delete_failed",
                extra={"document_id": str(doc.id), "error": str(exc)},
            )
            errors += 1

        doc.delete()  # CASCADE removes chunks, analysis, translations, chat sessions
        count += 1

    logger.info("expired_documents_deleted", extra={"count": count, "errors": errors})
    return {"deleted": count, "errors": errors}


@shared_task(name="tasks.maintenance.reset_daily_upload_counts")
def reset_daily_upload_counts() -> dict:
    from apps.users.models import User
    from django.utils.timezone import now

    today = now().date()
    updated = User.objects.filter(
        last_upload_reset__lt=today,
        daily_upload_count__gt=0,
    ).update(daily_upload_count=0, last_upload_reset=today)

    logger.info("daily_upload_counts_reset", extra={"users_reset": updated})
    return {"users_reset": updated}


@shared_task(name="tasks.maintenance.purge_deleted_users")
def purge_deleted_users() -> dict:
    from apps.users.models import User
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=30)
    qs = User.objects.filter(deleted_at__lt=cutoff, is_active=False)
    count, _ = qs.delete()
    logger.info("deleted_users_purged", extra={"count": count})
    return {"purged": count}
