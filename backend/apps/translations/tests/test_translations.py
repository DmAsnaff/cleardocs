"""
Tests for the translation pipeline and API endpoints.
LLM calls use MockProvider (LLM_PROVIDER='mock' in test settings).
"""
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.documents.models import Document
from apps.analysis.models import DocumentAnalysis
from apps.translations.models import Translation
from apps.documents.tests.factories import DocumentFactory
from apps.users.tests.factories import UserFactory


def _auth_client(user) -> APIClient:
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


def _make_done_doc_with_analysis(user):
    doc = DocumentFactory(user=user, status=Document.Status.DONE, extracted_text="Contract text.")
    DocumentAnalysis.objects.create(
        document=doc,
        summary="Summary.",
        simplified_text="Plain text.",
        key_points=["Point one.", "Point two."],
        clauses=[{"title": "Payment", "text": "...", "simplified": "Pay within 30 days.", "type": "obligation"}],
        risks=[{"title": "Risk 1", "description": "A risk.", "severity": "low", "recommendation": "Review."}],
    )
    return doc


# ---------------------------------------------------------------------------
# Translation task
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTranslationTask:
    def test_translate_creates_translation_record(self):
        from tasks.translation import translate_document
        user = UserFactory()
        doc = _make_done_doc_with_analysis(user)

        translate_document(str(doc.id), "es")

        translation = Translation.objects.get(document=doc, language="es")
        assert translation.status == Translation.Status.DONE
        assert translation.summary != ""
        assert isinstance(translation.clauses, list)

    def test_translate_is_idempotent(self):
        from tasks.translation import translate_document
        user = UserFactory()
        doc = _make_done_doc_with_analysis(user)

        translate_document(str(doc.id), "fr")
        translate_document(str(doc.id), "fr")  # second call — should skip

        assert Translation.objects.filter(document=doc, language="fr").count() == 1

    def test_translate_fails_gracefully_without_analysis(self):
        from tasks.translation import translate_document
        user = UserFactory()
        doc = DocumentFactory(user=user, status=Document.Status.DONE)

        translate_document(str(doc.id), "de")

        translation = Translation.objects.filter(document=doc, language="de").first()
        assert translation is None or translation.status == Translation.Status.FAILED


# ---------------------------------------------------------------------------
# Translation API endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTranslationEndpoints:
    def _url(self, doc_id, lang=None):
        base = f"/api/v1/documents/{doc_id}/translations/"
        return base if lang is None else base + f"{lang}/"

    def test_list_translations_empty(self):
        user = UserFactory()
        doc = _make_done_doc_with_analysis(user)
        client = _auth_client(user)

        resp = client.get(self._url(doc.id))
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_request_translation(self):
        user = UserFactory()
        doc = _make_done_doc_with_analysis(user)
        client = _auth_client(user)

        resp = client.post(self._url(doc.id), {"language": "es"}, format="json")
        assert resp.status_code in (200, 202)
        assert Translation.objects.filter(document=doc, language="es").exists()

    def test_request_translation_requires_done_status(self):
        user = UserFactory()
        doc = DocumentFactory(user=user, status=Document.Status.PENDING)
        client = _auth_client(user)

        resp = client.post(self._url(doc.id), {"language": "es"}, format="json")
        assert resp.status_code == 409

    def test_get_specific_translation(self):
        user = UserFactory()
        doc = _make_done_doc_with_analysis(user)
        Translation.objects.create(
            document=doc, language="es", status=Translation.Status.DONE,
            summary="Resumen.", simplified_text="Texto simple."
        )
        client = _auth_client(user)

        resp = client.get(self._url(doc.id, "es"))
        assert resp.status_code == 200
        assert resp.json()["data"]["summary"] == "Resumen."

    def test_get_nonexistent_translation_returns_404(self):
        user = UserFactory()
        doc = _make_done_doc_with_analysis(user)
        client = _auth_client(user)

        resp = client.get(self._url(doc.id, "zh"))
        assert resp.status_code == 404

    def test_translation_enforces_ownership(self):
        owner = UserFactory()
        attacker = UserFactory()
        doc = _make_done_doc_with_analysis(owner)
        client = _auth_client(attacker)

        resp = client.get(self._url(doc.id))
        assert resp.status_code == 403

    def test_invalid_language_code_rejected(self):
        user = UserFactory()
        doc = _make_done_doc_with_analysis(user)
        client = _auth_client(user)

        resp = client.post(self._url(doc.id), {"language": "not-a-lang-code-123"}, format="json")
        assert resp.status_code == 400
