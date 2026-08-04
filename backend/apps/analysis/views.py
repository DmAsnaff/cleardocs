import logging
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import Document
from .models import DocumentAnalysis
from .serializers import DocumentAnalysisSerializer, ClausesSerializer, RisksSerializer

logger = logging.getLogger(__name__)

_ANALYSIS_CACHE_TTL = 86_400  # 24 hours


def _success(data=None, message="", status_code=status.HTTP_200_OK):
    return Response({"status": "success", "message": message, "data": data}, status=status_code)


def _get_document_or_error(document_id: str, user) -> Document:
    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        raise NotFound("Document not found.")
    if doc.user_id != user.id:
        raise PermissionDenied("You do not have access to this document.")
    return doc


def _get_analysis_or_404(doc: Document) -> DocumentAnalysis:
    try:
        return DocumentAnalysis.objects.get(document=doc)
    except DocumentAnalysis.DoesNotExist:
        raise NotFound("Analysis not available yet. Check the document status.")


def _analysis_cache_key(document_id: str) -> str:
    return f"analysis:{document_id}"


class DocumentAnalysisView(APIView):
    """GET /api/v1/documents/{id}/analysis/ — full analysis result (cached 24h)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        doc = _get_document_or_error(document_id, request.user)

        cache_key = _analysis_cache_key(document_id)
        cached = cache.get(cache_key)
        if cached is not None:
            return _success(cached)

        analysis = _get_analysis_or_404(doc)
        data = DocumentAnalysisSerializer(analysis).data
        cache.set(cache_key, data, timeout=_ANALYSIS_CACHE_TTL)
        return _success(data)


class DocumentClausesView(APIView):
    """GET /api/v1/documents/{id}/analysis/clauses/ — clauses only."""
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        doc = _get_document_or_error(document_id, request.user)
        analysis = _get_analysis_or_404(doc)
        return _success(ClausesSerializer(analysis).data)


class DocumentRisksView(APIView):
    """GET /api/v1/documents/{id}/analysis/risks/ — risks only."""
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        doc = _get_document_or_error(document_id, request.user)
        analysis = _get_analysis_or_404(doc)
        return _success(RisksSerializer(analysis).data)


class DocumentExportView(APIView):
    """POST /api/v1/documents/{id}/analysis/export/ — download simplified PDF."""
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        doc = _get_document_or_error(document_id, request.user)
        analysis = _get_analysis_or_404(doc)

        try:
            from services.export.pdf_exporter import generate_pdf
            pdf_bytes = generate_pdf(doc, analysis)
        except Exception as exc:
            logger.error("export_failed", extra={"document_id": document_id, "error": str(exc)})
            return Response(
                {"status": "error", "message": "Export failed. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        stem = doc.original_filename.rsplit(".", 1)[0]
        filename = f"{stem}_simplified.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = len(pdf_bytes)
        logger.info("export_generated", extra={"document_id": document_id, "bytes": len(pdf_bytes)})
        return response
