"""
Tests for the AI analysis pipeline and API endpoints.

LLM calls are handled by MockProvider (LLM_PROVIDER='mock' in test settings).
Celery tasks run eagerly (CELERY_TASK_ALWAYS_EAGER=True).
"""
import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.documents.models import Document
from apps.analysis.models import DocumentAnalysis
from apps.documents.tests.factories import DocumentFactory
from apps.users.tests.factories import UserFactory


def _auth_client(user) -> APIClient:
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


# ---------------------------------------------------------------------------
# Analysis tasks (unit)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAnalysisTasks:
    def test_generate_summary_creates_analysis_record(self):
        from tasks.analysis import generate_summary
        user = UserFactory()
        doc = DocumentFactory(
            user=user,
            status=Document.Status.ANALYSING,
            extracted_text="This is a test contract for services rendered.",
            doc_category=Document.Category.LEGAL,
        )

        generate_summary(str(doc.id))

        analysis = DocumentAnalysis.objects.get(document=doc)
        assert analysis.summary != ""
        assert analysis.tokens_used > 0

    def test_extract_clauses_populates_clauses(self):
        from tasks.analysis import extract_clauses
        user = UserFactory()
        doc = DocumentFactory(
            user=user,
            status=Document.Status.ANALYSING,
            extracted_text="Payment is due within 30 days of invoice.",
            doc_category=Document.Category.FINANCIAL,
        )

        extract_clauses(str(doc.id))

        analysis = DocumentAnalysis.objects.get(document=doc)
        assert isinstance(analysis.clauses, list)
        assert len(analysis.clauses) > 0

    def test_extract_risks_populates_risks(self):
        from tasks.analysis import extract_risks
        user = UserFactory()
        doc = DocumentFactory(
            user=user,
            status=Document.Status.ANALYSING,
            extracted_text="The company may terminate this agreement without notice.",
        )

        extract_risks(str(doc.id))

        analysis = DocumentAnalysis.objects.get(document=doc)
        assert isinstance(analysis.risks, list)

    def test_extract_dates_populates_key_dates(self):
        from tasks.analysis import extract_dates
        user = UserFactory()
        doc = DocumentFactory(
            user=user,
            status=Document.Status.ANALYSING,
            extracted_text="This agreement is effective January 1, 2025.",
        )

        extract_dates(str(doc.id))

        analysis = DocumentAnalysis.objects.get(document=doc)
        assert isinstance(analysis.key_dates, list)

    def test_finalise_analysis_returns_document_id(self):
        from tasks.analysis import finalise_analysis, generate_summary
        user = UserFactory()
        doc = DocumentFactory(
            user=user,
            status=Document.Status.ANALYSING,
            extracted_text="Contract text here.",
        )
        generate_summary(str(doc.id))  # ensure analysis record exists

        result = finalise_analysis([str(doc.id)] * 4, str(doc.id))
        assert result == str(doc.id)

    def test_generate_embeddings_stores_vectors(self):
        from tasks.analysis import generate_embeddings
        from apps.documents.models import DocumentChunk
        user = UserFactory()
        doc = DocumentFactory(user=user, status=Document.Status.ANALYSING)
        DocumentChunk.objects.create(document=doc, chunk_index=0, text="chunk text", token_count=5)

        generate_embeddings(str(doc.id))

        chunk = DocumentChunk.objects.get(document=doc)
        assert chunk.embedding is not None
        assert len(chunk.embedding) == 1536


# ---------------------------------------------------------------------------
# Token budget
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTokenBudget:
    def test_check_document_budget_raises_when_exceeded(self):
        from services.llm.token_budget import check_document_budget, TokenBudgetExceeded
        with pytest.raises(TokenBudgetExceeded):
            check_document_budget(99_000, 2_000)

    def test_check_document_budget_passes_under_limit(self):
        from services.llm.token_budget import check_document_budget
        check_document_budget(50_000, 10_000)  # should not raise

    def test_add_and_get_user_tokens(self):
        from services.llm.token_budget import add_user_tokens, get_user_tokens_today
        user = UserFactory()
        uid = str(user.id)

        add_user_tokens(uid, 1000)
        add_user_tokens(uid, 500)
        total = get_user_tokens_today(uid)
        assert total >= 1500

    def test_check_user_daily_budget_raises_when_exceeded(self):
        from services.llm.token_budget import add_user_tokens, check_user_daily_budget, TokenBudgetExceeded
        user = UserFactory()
        uid = str(user.id)

        add_user_tokens(uid, 499_000)
        with pytest.raises(TokenBudgetExceeded):
            check_user_daily_budget(uid, 2_000)


# ---------------------------------------------------------------------------
# Analysis API endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAnalysisEndpoints:
    def _make_analysis(self, user):
        doc = DocumentFactory(user=user, status=Document.Status.DONE)
        analysis = DocumentAnalysis.objects.create(
            document=doc,
            summary="A summary.",
            simplified_text="Plain text.",
            clauses=[{"title": "Clause 1", "text": "...", "simplified": "...", "type": "general"}],
            risks=[{"title": "Risk 1", "description": "...", "severity": "low", "recommendation": "..."}],
            key_dates=[{"label": "Start Date", "date": "2025-01-01", "relative": None, "description": "..."}],
        )
        return doc, analysis

    def test_get_full_analysis(self):
        user = UserFactory()
        doc, _ = self._make_analysis(user)
        client = _auth_client(user)

        resp = client.get(f"/api/v1/documents/{doc.id}/analysis/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["summary"] == "A summary."
        assert len(data["clauses"]) == 1
        assert len(data["risks"]) == 1

    def test_get_clauses_only(self):
        user = UserFactory()
        doc, _ = self._make_analysis(user)
        client = _auth_client(user)

        resp = client.get(f"/api/v1/documents/{doc.id}/analysis/clauses/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "clauses" in data
        assert "summary" not in data

    def test_get_risks_only(self):
        user = UserFactory()
        doc, _ = self._make_analysis(user)
        client = _auth_client(user)

        resp = client.get(f"/api/v1/documents/{doc.id}/analysis/risks/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "risks" in data
        assert "clauses" not in data

    def test_analysis_not_found_before_processing(self):
        user = UserFactory()
        doc = DocumentFactory(user=user, status=Document.Status.PENDING)
        client = _auth_client(user)

        resp = client.get(f"/api/v1/documents/{doc.id}/analysis/")
        assert resp.status_code == 404

    def test_analysis_enforces_ownership(self):
        owner = UserFactory()
        attacker = UserFactory()
        doc, _ = self._make_analysis(owner)
        client = _auth_client(attacker)

        resp = client.get(f"/api/v1/documents/{doc.id}/analysis/")
        assert resp.status_code == 403

    def test_analysis_requires_auth(self):
        owner = UserFactory()
        doc, _ = self._make_analysis(owner)

        resp = APIClient().get(f"/api/v1/documents/{doc.id}/analysis/")
        assert resp.status_code == 401
