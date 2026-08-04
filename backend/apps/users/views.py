from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView as BaseTokenRefreshView

from .models import User
from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
)

REFRESH_COOKIE = "refresh_token"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds


def _set_refresh_cookie(response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        max_age=COOKIE_MAX_AGE,
    )


def _success(data=None, message="", status_code=status.HTTP_200_OK):
    return Response({"status": "success", "message": message, "data": data}, status=status_code)


def _error(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({"status": "error", "message": message, "errors": errors or {}}, status=status_code)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return _error("Registration failed.", serializer.errors, status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        return _success(
            UserProfileSerializer(user).data,
            "Account created. Check your email to verify your account.",
            status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            refresh_token = response.data.pop("refresh", None)
            if refresh_token:
                _set_refresh_cookie(response, refresh_token)
            # Wrap in envelope
            response.data = {
                "status": "success",
                "message": "Login successful.",
                "data": {"access": response.data.get("access")},
            }
        return response


class TokenRefreshView(BaseTokenRefreshView):
    def post(self, request, *args, **kwargs):
        # Read refresh token from HttpOnly cookie if not in body
        if REFRESH_COOKIE in request.COOKIES and "refresh" not in request.data:
            request.data["refresh"] = request.COOKIES[REFRESH_COOKIE]

        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            new_refresh = response.data.pop("refresh", None)
            if new_refresh:
                _set_refresh_cookie(response, new_refresh)
            response.data = {
                "status": "success",
                "message": "Token refreshed.",
                "data": {"access": response.data.get("access")},
            }
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(REFRESH_COOKIE) or request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass  # Already invalid — that's fine

        response = _success(message="Logged out successfully.")
        response.delete_cookie(REFRESH_COOKIE)
        return response


class EmailVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return _error("Verification failed.", serializer.errors)
        serializer.save()
        return _success(message="Email verified. You can now log in.")


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return _error("Invalid request.", serializer.errors)
        serializer.save()
        # Always return success — no email enumeration
        return _success(message="If that email exists, a reset link has been sent.")


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return _error("Password reset failed.", serializer.errors)
        serializer.save()
        return _success(message="Password reset successfully. You can now log in.")


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return _success(UserProfileSerializer(request.user).data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return _error("Update failed.", serializer.errors)
        serializer.save()
        return _success(serializer.data, "Profile updated.")

    def delete(self, request):
        user = request.user
        # Soft delete — keeps audit trail, purge handled by Celery Beat
        user.deleted_at = timezone.now()
        user.is_active = False
        user.save(update_fields=["deleted_at", "is_active"])

        response = _success(message="Account deleted. Your data will be purged within 30 days.")
        response.delete_cookie(REFRESH_COOKIE)
        return response


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return _error("Password change failed.", serializer.errors)
        serializer.save()
        return _success(message="Password changed successfully.")


class DataExportView(APIView):
    """GET /api/v1/auth/me/data-export/ — download all user data as JSON (GDPR)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        import json
        from django.http import HttpResponse
        from django.db.models import Count
        from apps.documents.models import Document
        from apps.translations.models import Translation
        from apps.chat.models import ChatSession

        user = request.user

        doc_rows = list(
            Document.objects.filter(user=user).order_by("-uploaded_at").values(
                "id", "original_filename", "doc_category", "status",
                "uploaded_at", "processed_at", "expires_at",
            )
        )
        doc_ids = [str(d["id"]) for d in doc_rows]

        trans_map: dict[str, list] = {}
        for t in Translation.objects.filter(document_id__in=doc_ids).values(
            "document_id", "language", "status", "created_at"
        ):
            trans_map.setdefault(str(t["document_id"]), []).append({
                "language": t["language"],
                "status": t["status"],
                "created_at": t["created_at"].isoformat() if t["created_at"] else None,
            })

        chat_map: dict[str, int] = {
            str(row["document_id"]): row["count"]
            for row in (
                ChatSession.objects
                .filter(document_id__in=doc_ids)
                .values("document_id")
                .annotate(count=Count("id"))
            )
        }

        documents = []
        for d in doc_rows:
            did = str(d["id"])
            documents.append({
                "id": did,
                "original_filename": d["original_filename"],
                "doc_category": d["doc_category"],
                "status": d["status"],
                "uploaded_at": d["uploaded_at"].isoformat() if d["uploaded_at"] else None,
                "processed_at": d["processed_at"].isoformat() if d["processed_at"] else None,
                "expires_at": d["expires_at"].isoformat() if d["expires_at"] else None,
                "translations": trans_map.get(did, []),
                "chat_sessions": chat_map.get(did, 0),
            })

        export = {
            "exported_at": timezone.now().isoformat(),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "preferred_language": user.preferred_language,
                "date_joined": user.date_joined.isoformat(),
            },
            "documents": documents,
        }

        response = HttpResponse(json.dumps(export, indent=2), content_type="application/json")
        response["Content-Disposition"] = 'attachment; filename="my_cleardocs_data.json"'
        return response
