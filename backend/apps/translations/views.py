import logging
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import Document
from .models import Translation
from .serializers import TranslationSerializer, TranslationRequestSerializer

logger = logging.getLogger(__name__)


def _success(data=None, message="", status_code=status.HTTP_200_OK):
    return Response({"status": "success", "message": message, "data": data}, status=status_code)


def _error(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({"status": "error", "message": message, "errors": errors or {}}, status=status_code)


def _get_document_or_error(document_id: str, user) -> Document:
    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        raise NotFound("Document not found.")
    if doc.user_id != user.id:
        raise PermissionDenied("You do not have access to this document.")
    return doc


class TranslationListCreateView(APIView):
    """
    GET  /api/v1/documents/{id}/translations/  — list all translations for document
    POST /api/v1/documents/{id}/translations/  — request a new translation
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        doc = _get_document_or_error(document_id, request.user)
        translations = Translation.objects.filter(document=doc)
        return _success(TranslationSerializer(translations, many=True).data)

    def post(self, request, document_id):
        doc = _get_document_or_error(document_id, request.user)

        if doc.status != Document.Status.DONE:
            return _error(
                "Document must be fully processed before requesting a translation.",
                status_code=status.HTTP_409_CONFLICT,
            )

        serializer = TranslationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return _error("Invalid request.", serializer.errors)

        language = serializer.validated_data["language"]

        # Don't re-run if already done or processing
        existing = Translation.objects.filter(document=doc, language=language).first()
        if existing and existing.status in (Translation.Status.DONE, Translation.Status.PROCESSING):
            return _success(
                TranslationSerializer(existing).data,
                "Translation already exists." if existing.status == Translation.Status.DONE
                else "Translation is already in progress.",
            )

        # Create or reset failed record
        translation, _ = Translation.objects.update_or_create(
            document=doc,
            language=language,
            defaults={"status": Translation.Status.PENDING, "error_message": None},
        )

        from tasks.translation import translate_document
        translate_document.delay(str(doc.id), language)

        logger.info(
            "translation_requested",
            extra={"document_id": str(doc.id), "language": language},
        )
        return _success(
            TranslationSerializer(translation).data,
            "Translation started.",
            status.HTTP_202_ACCEPTED,
        )


class TranslationDetailView(APIView):
    """GET /api/v1/documents/{id}/translations/{language}/ — get a specific translation."""
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id, language):
        doc = _get_document_or_error(document_id, request.user)
        try:
            translation = Translation.objects.get(document=doc, language=language)
        except Translation.DoesNotExist:
            raise NotFound(f"No translation found for language '{language}'.")
        return _success(TranslationSerializer(translation).data)
