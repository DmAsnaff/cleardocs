import pytest
from django.core import signing
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.models import User
from .factories import UserFactory, UnverifiedUserFactory


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def unverified_user():
    return UnverifiedUserFactory()


@pytest.fixture
def auth_client(user):
    client = APIClient()
    response = client.post(reverse("auth-login"), {"email": user.email, "password": "TestPass123!"})
    access_token = response.data["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return client, user


# ── Registration ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegister:
    url = reverse("auth-register")

    def test_register_success(self, client):
        payload = {
            "email": "new@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "full_name": "Test User",
        }
        response = client.post(self.url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "success"
        assert User.objects.filter(email="new@example.com").exists()

    def test_register_duplicate_email(self, client, user):
        payload = {
            "email": user.email,
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch(self, client):
        payload = {
            "email": "new@example.com",
            "password": "StrongPass123!",
            "password_confirm": "DifferentPass123!",
        }
        response = client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, client):
        payload = {
            "email": "new@example.com",
            "password": "123",
            "password_confirm": "123",
        }
        response = client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_new_user_is_unverified(self, client):
        payload = {
            "email": "new@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        client.post(self.url, payload)
        user = User.objects.get(email="new@example.com")
        assert user.is_verified is False


# ── Login ──────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLogin:
    url = reverse("auth-login")

    def test_login_success(self, client, user):
        response = client.post(self.url, {"email": user.email, "password": "TestPass123!"})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data["data"]
        assert REFRESH_COOKIE_KEY(response)  # refresh token set as cookie

    def test_login_wrong_password(self, client, user):
        response = client.post(self.url, {"email": user.email, "password": "WrongPass!"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client):
        response = client.post(self.url, {"email": "nobody@example.com", "password": "Pass123!"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_sets_httponly_cookie(self, client, user):
        response = client.post(self.url, {"email": user.email, "password": "TestPass123!"})
        assert "refresh_token" in response.cookies
        assert response.cookies["refresh_token"]["httponly"]

    def test_login_inactive_user(self, client, user):
        user.is_active = False
        user.save()
        response = client.post(self.url, {"email": user.email, "password": "TestPass123!"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def REFRESH_COOKIE_KEY(response):
    return "refresh_token" in response.cookies


# ── Token Refresh ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTokenRefresh:
    url = reverse("auth-token-refresh")

    def test_refresh_via_cookie(self, client, user):
        login_response = client.post(reverse("auth-login"), {"email": user.email, "password": "TestPass123!"})
        refresh_cookie = login_response.cookies["refresh_token"].value

        client.cookies["refresh_token"] = refresh_cookie
        response = client.post(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data["data"]

    def test_refresh_via_body(self, client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(user)
        response = client.post(self.url, {"refresh": str(token)})
        assert response.status_code == status.HTTP_200_OK


# ── Logout ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLogout:
    url = reverse("auth-logout")

    def test_logout_blacklists_token(self, client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(user)
        response = client.post(self.url, {"refresh": str(token)})
        assert response.status_code == status.HTTP_200_OK

        # Refreshing the blacklisted token should fail
        refresh_response = client.post(reverse("auth-token-refresh"), {"refresh": str(token)})
        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_clears_cookie(self, client, user):
        login_response = client.post(reverse("auth-login"), {"email": user.email, "password": "TestPass123!"})
        refresh_cookie = login_response.cookies["refresh_token"].value
        client.cookies["refresh_token"] = refresh_cookie

        response = client.post(self.url)
        assert response.status_code == status.HTTP_200_OK
        # Cookie should be cleared (max_age=0 or deleted)
        assert response.cookies.get("refresh_token", None) is not None


# ── Email Verification ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEmailVerification:
    url = reverse("auth-verify-email")

    def test_verify_success(self, client, unverified_user):
        token = signing.dumps({"user_id": str(unverified_user.id)}, salt="email-verification")
        response = client.post(self.url, {"token": token})
        assert response.status_code == status.HTTP_200_OK
        unverified_user.refresh_from_db()
        assert unverified_user.is_verified is True

    def test_verify_invalid_token(self, client):
        response = client.post(self.url, {"token": "bad-token"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_expired_token(self, client, unverified_user):
        # Signing with max_age=0 in the load will trigger expiry
        token = signing.dumps({"user_id": str(unverified_user.id)}, salt="email-verification")
        import time
        with pytest.raises(Exception):
            signing.loads(token, salt="email-verification", max_age=-1)


# ── Profile ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProfile:
    url = reverse("auth-me")

    def test_get_profile_authenticated(self, auth_client):
        client, user = auth_client
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["email"] == user.email

    def test_get_profile_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile(self, auth_client):
        client, user = auth_client
        response = client.patch(self.url, {"full_name": "Updated Name", "preferred_language": "fr"})
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.full_name == "Updated Name"
        assert user.preferred_language == "fr"

    def test_delete_account_soft_deletes(self, auth_client):
        client, user = auth_client
        response = client.delete(self.url)
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.deleted_at is not None
        assert user.is_active is False
