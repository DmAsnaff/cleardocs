"""
Tests for document upload, list, detail, delete, and status endpoints.
All Celery tasks run eagerly in test settings (CELERY_TASK_ALWAYS_EAGER=True).
Storage and virus-scan calls are mocked to keep tests fast and hermetic.
"""
import io
import uuid
from unittest.mock import patch, MagicMock

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.documents.models import Document
from apps.users.tests.factories import UserFactory
from .factories import DocumentFactory

LIST_URL = "/api/v1/documents/"


def _auth_client(user) -> APIClient:
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


def _pdf_file(name="test.pdf", size=1024):
    content = b"%PDF-1.4 fake pdf content " + b"x" * size
    return io.BytesIO(content), name


# ---------------------------------------------------------------------------
# Upload (POST /api/v1/documents/)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDocumentUpload:
    @patch("tasks.pipeline.process_document")
    @patch("services.storage.s3_client.storage_service.upload", return_value=("uploads/test.pdf", "local"))
    @patch("apps.documents.views.validate_upload", return_value="application/pdf")
    def test_upload_success(self, mock_validate, mock_upload, mock_pipeline):
        user = UserFactory()
        client = _auth_client(user)

        data = {"file": io.BytesIO(b"%PDF-1.4 content"), "doc_category": "legal", "target_language": "en"}
        data["file"].name = "contract.pdf"

        resp = client.post(LIST_URL, data, format="multipart")

        assert resp.status_code == status.HTTP_201_CREATED
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["original_filename"] == "contract.pdf"
        assert body["data"]["status"] == Document.Status.PENDING
        mock_pipeline.assert_called_once()

    def test_upload_requires_auth(self):
        client = APIClient()
        buf = io.BytesIO(b"%PDF-1.4 content")
        buf.name = "file.pdf"
        resp = client.post(LIST_URL, {"file": buf}, format="multipart")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("apps.documents.views.validate_upload", side_effect=Exception("File too large."))
    def test_upload_rejects_oversized_file(self, mock_validate):
        user = UserFactory()
        client = _auth_client(user)
        buf = io.BytesIO(b"%PDF-1.4 x" * 100)
        buf.name = "big.pdf"
        resp = client.post(LIST_URL, {"file": buf}, format="multipart")
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("apps.documents.validators.validate_upload", return_value="application/pdf")
    @patch("services.storage.s3_client.storage_service.upload", side_effect=Exception("S3 down"))
    def test_upload_storage_failure_returns_500(self, mock_upload, mock_validate):
        user = UserFactory()
        client = _auth_client(user)
        buf = io.BytesIO(b"%PDF-1.4 content")
        buf.name = "test.pdf"
        resp = client.post(LIST_URL, {"file": buf}, format="multipart")
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_upload_no_file_returns_400(self):
        user = UserFactory()
        client = _auth_client(user)
        resp = client.post(LIST_URL, {}, format="multipart")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# List (GET /api/v1/documents/)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDocumentList:
    def test_list_returns_own_documents_only(self):
        user_a = UserFactory()
        user_b = UserFactory()
        DocumentFactory(user=user_a, status=Document.Status.DONE)
        DocumentFactory(user=user_a, status=Document.Status.DONE)
        DocumentFactory(user=user_b, status=Document.Status.DONE)

        client = _auth_client(user_a)
        resp = client.get(LIST_URL)

        assert resp.status_code == status.HTTP_200_OK
        results = resp.json()["results"]
        assert len(results) == 2

    def test_list_excludes_failed_documents(self):
        user = UserFactory()
        DocumentFactory(user=user, status=Document.Status.DONE)
        DocumentFactory(user=user, status=Document.Status.FAILED)

        client = _auth_client(user)
        resp = client.get(LIST_URL)

        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["status"] == Document.Status.DONE

    def test_list_filters_by_category(self):
        user = UserFactory()
        DocumentFactory(user=user, status=Document.Status.DONE, doc_category=Document.Category.LEGAL)
        DocumentFactory(user=user, status=Document.Status.DONE, doc_category=Document.Category.MEDICAL)

        client = _auth_client(user)
        resp = client.get(LIST_URL + "?category=legal")

        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["doc_category"] == Document.Category.LEGAL

    def test_list_requires_auth(self):
        resp = APIClient().get(LIST_URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Detail (GET /DELETE /api/v1/documents/<id>/)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDocumentDetail:
    def test_get_own_document(self):
        user = UserFactory()
        doc = DocumentFactory(user=user, status=Document.Status.DONE)
        client = _auth_client(user)

        resp = client.get(f"{LIST_URL}{doc.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"]["id"] == str(doc.id)

    def test_get_other_users_document_returns_403(self):
        owner = UserFactory()
        attacker = UserFactory()
        doc = DocumentFactory(user=owner)

        client = _auth_client(attacker)
        resp = client.get(f"{LIST_URL}{doc.id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_get_nonexistent_document_returns_404(self):
        user = UserFactory()
        client = _auth_client(user)
        resp = client.get(f"{LIST_URL}{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    @patch("services.storage.s3_client.storage_service.delete")
    def test_delete_own_document(self, mock_delete):
        user = UserFactory()
        doc = DocumentFactory(user=user)
        client = _auth_client(user)

        resp = client.delete(f"{LIST_URL}{doc.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert not Document.objects.filter(id=doc.id).exists()
        mock_delete.assert_called_once()

    def test_delete_other_users_document_returns_403(self):
        owner = UserFactory()
        attacker = UserFactory()
        doc = DocumentFactory(user=owner)

        client = _auth_client(attacker)
        resp = client.delete(f"{LIST_URL}{doc.id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert Document.objects.filter(id=doc.id).exists()

    @patch("services.storage.s3_client.storage_service.delete", side_effect=Exception("S3 error"))
    def test_delete_continues_if_storage_fails(self, mock_delete):
        """Storage failure is logged but the DB record is still deleted."""
        user = UserFactory()
        doc = DocumentFactory(user=user)
        client = _auth_client(user)

        resp = client.delete(f"{LIST_URL}{doc.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert not Document.objects.filter(id=doc.id).exists()


# ---------------------------------------------------------------------------
# Status (GET /api/v1/documents/<id>/status/)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDocumentStatus:
    def test_status_returns_lightweight_payload(self):
        user = UserFactory()
        doc = DocumentFactory(user=user, status=Document.Status.ANALYSING)
        client = _auth_client(user)

        resp = client.get(f"{LIST_URL}{doc.id}/status/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()["data"]
        assert data["status"] == Document.Status.ANALYSING
        assert "id" in data
        assert "error_message" in data
        assert "original_filename" not in data  # lightweight — not in DocumentStatusSerializer

    def test_status_enforces_ownership(self):
        owner = UserFactory()
        other = UserFactory()
        doc = DocumentFactory(user=owner)

        client = _auth_client(other)
        resp = client.get(f"{LIST_URL}{doc.id}/status/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
