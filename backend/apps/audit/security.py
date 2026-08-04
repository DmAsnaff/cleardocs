"""
Security headers middleware — adds CSP and other defensive headers
on every response.  Django's built-in settings handle HSTS/XSS/nosniff;
this adds the CSP header which needs to be constructed dynamically.
"""
from django.conf import settings


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._add_headers(response)
        return response

    def _add_headers(self, response) -> None:
        # Content-Security-Policy — restrictive by default, relaxed in DEBUG
        if not settings.DEBUG:
            csp = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "   # Tailwind needs this
                "img-src 'self' data: blob:; "          # blob: for PDF.js
                "font-src 'self'; "
                "connect-src 'self' wss:; "             # WebSocket
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
            response.setdefault("Content-Security-Policy", csp)

        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("X-Frame-Options", "DENY")
        response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
