"""
Load test — 50 concurrent users uploading documents and browsing analysis.

Usage:
  pip install locust
  locust -f locustfile.py --host http://localhost:8000 -u 50 -r 5 --headless -t 2m
"""
import io
import random
from locust import HttpUser, task, between

# Minimal valid PDF (1 page, 190 bytes)
_TINY_PDF = (
    b"%PDF-1.4 1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj "
    b"xref 0 4 "
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>startxref 190 %%EOF"
)

_CATEGORIES = ["legal", "medical", "government", "financial", "other"]


class ClearDocsUser(HttpUser):
    """Simulates a registered user: login → upload → browse → analyse."""

    wait_time = between(1, 3)

    # Populated on login
    _access_token: str | None = None
    _doc_ids: list[str]

    # Override in environment — default matches docker-compose dev setup
    test_email = "loadtest@cleardocs.test"
    test_password = "LoadTest_Passw0rd!"

    def on_start(self) -> None:
        self._doc_ids = []
        self._login()

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def _login(self) -> None:
        with self.client.post(
            "/api/v1/auth/login/",
            json={"email": self.test_email, "password": self.test_password},
            catch_response=True,
            name="/auth/login",
        ) as resp:
            if resp.status_code == 200:
                self._access_token = resp.json()["data"]["access"]
            else:
                resp.failure(f"Login failed: {resp.status_code}")

    def _headers(self) -> dict:
        if self._access_token:
            return {"Authorization": f"Bearer {self._access_token}"}
        return {}

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    @task(3)
    def upload_document(self) -> None:
        pdf = io.BytesIO(_TINY_PDF)
        with self.client.post(
            "/api/v1/documents/",
            files={"file": ("load_test.pdf", pdf, "application/pdf")},
            data={"doc_category": random.choice(_CATEGORIES)},
            headers=self._headers(),
            catch_response=True,
            name="/documents/ [upload]",
        ) as resp:
            if resp.status_code == 201:
                doc_id = resp.json().get("data", {}).get("id")
                if doc_id:
                    self._doc_ids.append(doc_id)
            elif resp.status_code == 401:
                self._login()
            else:
                resp.failure(f"Upload {resp.status_code}: {resp.text[:120]}")

    @task(6)
    def list_documents(self) -> None:
        self.client.get(
            "/api/v1/documents/",
            headers=self._headers(),
            name="/documents/ [list]",
        )

    @task(2)
    def search_documents(self) -> None:
        self.client.get(
            "/api/v1/documents/?search=contract",
            headers=self._headers(),
            name="/documents/ [search]",
        )

    @task(3)
    def poll_status(self) -> None:
        if not self._doc_ids:
            return
        doc_id = random.choice(self._doc_ids)
        self.client.get(
            f"/api/v1/documents/{doc_id}/status/",
            headers=self._headers(),
            name="/documents/{id}/status/",
        )

    @task(2)
    def view_analysis(self) -> None:
        if not self._doc_ids:
            return
        doc_id = random.choice(self._doc_ids)
        with self.client.get(
            f"/api/v1/documents/{doc_id}/analysis/",
            headers=self._headers(),
            catch_response=True,
            name="/documents/{id}/analysis/",
        ) as resp:
            # 404 is expected when analysis isn't ready yet — not a failure
            if resp.status_code in (200, 404):
                resp.success()

    @task(1)
    def get_profile(self) -> None:
        self.client.get(
            "/api/v1/auth/me/",
            headers=self._headers(),
            name="/auth/me/",
        )
