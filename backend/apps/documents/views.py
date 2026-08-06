import logging
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Document
from .serializers import DocumentSerializer, DocumentStatusSerializer, DocumentUploadSerializer
from .validators import validate_upload

logger = logging.getLogger(__name__)


def _success(data=None, message="", status_code=status.HTTP_200_OK):
    return Response({"status": "success", "message": message, "data": data}, status=status_code)


def _error(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({"status": "error", "message": message, "errors": errors or {}}, status=status_code)


def _get_document_or_404(document_id: str, user) -> Document:
    """Fetch document, enforce ownership — no IDOR."""
    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        raise NotFound("Document not found.")
    if doc.user_id != user.id:
        raise PermissionDenied("You do not have access to this document.")
    return doc


class DocumentPagination(CursorPagination):
    page_size = 20
    ordering = "-uploaded_at"


class DocumentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            Document.objects
            .filter(user=request.user)
            .order_by("-uploaded_at")
        )

        category = request.query_params.get("category")
        if category:
            qs = qs.filter(doc_category=category)

        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        else:
            # Hide failed documents from the default list; they remain
            # reachable via an explicit ?status=failed filter.
            qs = qs.exclude(status=Document.Status.FAILED)

        search = request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(original_filename__icontains=search)

        paginator = DocumentPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = DocumentSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return _error("Invalid request.", serializer.errors)

        uploaded_file = serializer.validated_data["file"]

        # Validate file content (MIME, extension, size)
        try:
            mime_type = validate_upload(uploaded_file)
        except Exception as exc:
            return _error(str(exc), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Read file bytes once
        file_bytes = uploaded_file.read()

        # Save to storage (local or S3)
        from services.storage.s3_client import storage_service
        try:
            s3_key, s3_bucket = storage_service.upload(
                file_bytes, uploaded_file.name, mime_type
            )
        except Exception as exc:
            logger.error("storage_upload_failed", extra={"error": str(exc)})
            return _error("Failed to store file. Please try again.", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Create Document record
        doc = Document.objects.create(
            user=request.user,
            original_filename=uploaded_file.name,
            s3_key=s3_key,
            s3_bucket=s3_bucket,
            mime_type=mime_type,
            file_size_bytes=len(file_bytes),
            doc_category=serializer.validated_data.get("doc_category", Document.Category.OTHER),
            target_language=serializer.validated_data.get("target_language", "en"),
            status=Document.Status.PENDING,
        )

        # Kick off the Celery pipeline
        from tasks.pipeline import process_document
        process_document(str(doc.id))

        logger.info("document_uploaded", extra={"document_id": str(doc.id), "user_id": str(request.user.id)})
        return _success(
            DocumentSerializer(doc).data,
            "Document uploaded. Processing has started.",
            status.HTTP_201_CREATED,
        )


class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        doc = _get_document_or_404(document_id, request.user)
        return _success(DocumentSerializer(doc, context={"request": request}).data)

    def delete(self, request, document_id):
        doc = _get_document_or_404(document_id, request.user)

        # Delete from storage
        from services.storage.s3_client import storage_service
        try:
            storage_service.delete(doc.s3_key, doc.s3_bucket)
        except Exception as exc:
            logger.warning("storage_delete_failed", extra={"error": str(exc), "document_id": document_id})

        doc.delete()
        return _success(message="Document deleted.")


class DocumentStatusView(APIView):
    """Lightweight polling endpoint — backup to WebSocket."""
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        doc = _get_document_or_404(document_id, request.user)
        return _success(DocumentStatusSerializer(doc).data)
