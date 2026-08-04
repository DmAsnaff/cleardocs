import logging

logger = logging.getLogger(__name__)

# Paths that trigger a DB audit log entry (beyond JSON logging)
_AUDITED_PREFIXES = ("/api/v1/auth/", "/api/v1/documents/")
_SKIP_PREFIXES = ("/health", "/static", "/admin/jsi18n")

# Map (method, path fragment) → action label
_ACTION_MAP = [
    ("POST", "/auth/login", "auth.login"),
    ("POST", "/auth/logout", "auth.logout"),
    ("POST", "/auth/register", "auth.register"),
    ("DELETE", "/auth/me", "user.delete"),
    ("POST", "/documents/", "document.upload"),
    ("DELETE", "/documents/", "document.delete"),
    ("POST", "/analysis/export/", "document.export"),
    ("POST", "/translations/", "translation.request"),
]


def _resolve_action(method: str, path: str) -> str:
    for m, fragment, label in _ACTION_MAP:
        if method == m and fragment in path:
            return label
    return f"{method.lower()}.{path.split('/')[3] if len(path.split('/')) > 3 else 'request'}"


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        path = request.path
        if any(path.startswith(p) for p in _SKIP_PREFIXES):
            return response

        # Always log to structured JSON
        logger.info(
            "api_request",
            extra={
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
                "user_id": str(request.user.id) if request.user.is_authenticated else None,
                "ip": request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR")),
            },
        )

        # Write significant events to the audit_logs table
        if any(path.startswith(p) for p in _AUDITED_PREFIXES):
            self._persist(request, response)

        return response

    def _persist(self, request, response) -> None:
        """Best-effort DB write — never raises."""
        try:
            from django.db import transaction
            from .models import AuditLog

            user = request.user if request.user.is_authenticated else None
            action = _resolve_action(request.method, request.path)
            ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR"))
            if ip:
                ip = ip.split(",")[0].strip()

            # Extract resource_id from URL path segments
            parts = [p for p in request.path.split("/") if p]
            resource_id = ""
            for i, part in enumerate(parts):
                if part in ("documents", "sessions") and i + 1 < len(parts):
                    resource_id = parts[i + 1]
                    break

            def _write():
                AuditLog.objects.create(
                    user=user,
                    action=action,
                    resource_id=resource_id,
                    ip_address=ip or None,
                    status_code=response.status_code,
                )

            transaction.on_commit(_write)
        except Exception:
            pass  # Never let audit logging crash a request
