from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "password", "password_confirm", "full_name")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        self._send_verification_email(user)
        return user

    def _send_verification_email(self, user):
        token = signing.dumps({"user_id": str(user.id)}, salt="email-verification")
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost")
        verify_url = f"{frontend_url}/verify-email?token={token}"
        send_mail(
            subject="Verify your ClearDocs email",
            message=f"Click the link to verify your email: {verify_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "preferred_language", "role", "is_verified", "created_at")
        read_only_fields = ("id", "email", "role", "is_verified", "created_at")


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, token):
        try:
            data = signing.loads(token, salt="email-verification", max_age=86400)  # 24h
        except signing.SignatureExpired:
            raise serializers.ValidationError("Verification link has expired.")
        except signing.BadSignature:
            raise serializers.ValidationError("Invalid verification link.")

        try:
            self._user = User.objects.get(id=data["user_id"])
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        return token

    def save(self):
        self._user.is_verified = True
        self._user.save(update_fields=["is_verified"])
        return self._user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        # Always return success to avoid email enumeration
        self._email = email
        return email

    def save(self):
        try:
            user = User.objects.get(email=self._email, is_active=True, deleted_at__isnull=True)
        except User.DoesNotExist:
            return  # Silently ignore — no email enumeration

        token = signing.dumps({"user_id": str(user.id)}, salt="password-reset")
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost")
        reset_url = f"{frontend_url}/reset-password?token={token}"
        send_mail(
            subject="Reset your ClearDocs password",
            message=f"Click the link to reset your password (valid for 1 hour): {reset_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(validators=[validate_password])
    password_confirm = serializers.CharField()

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def validate_token(self, token):
        try:
            data = signing.loads(token, salt="password-reset", max_age=3600)  # 1h
        except signing.SignatureExpired:
            raise serializers.ValidationError("Password reset link has expired.")
        except signing.BadSignature:
            raise serializers.ValidationError("Invalid password reset link.")

        try:
            self._user = User.objects.get(id=data["user_id"])
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        return token

    def save(self):
        self._user.set_password(self.validated_data["password"])
        self._user.save(update_fields=["password"])
        return self._user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        return attrs

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
