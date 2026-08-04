from .base import *  # noqa

DEBUG = False

ALLOWED_HOSTS = [
    os.environ.get("ALLOWED_HOST", "api.cleardocs.app"),
    # ALB health check uses the container's private IP
    os.environ.get("ECS_CONTAINER_METADATA_URI_V4", "").split("/")[-1] or "localhost",
]

CORS_ALLOWED_ORIGINS = [
    "https://cleardocs.app",
    "https://www.cleardocs.app",
]

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

CLAMAV_ENABLED = True

# Security hardening
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # ALB terminates TLS

# DB connection pooling — keep connections alive between requests
DATABASES["default"]["CONN_MAX_AGE"] = 60
DATABASES["default"]["OPTIONS"] = {"connect_timeout": 10}

# Sentry error tracking
_sentry_dsn = os.environ.get("SENTRY_DSN", "")
if _sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        send_default_pii=False,
        environment="production",
    )
