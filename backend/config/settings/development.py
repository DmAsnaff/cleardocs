from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Show emails in console during development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable virus scanning locally if ClamAV not running
CLAMAV_ENABLED = False

# Disable real S3 — use local filesystem storage in development
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# Lower token budget for dev/testing
MAX_TOKENS_PER_DOCUMENT = 10_000

# CORS in development. The frontend sends credentials (withCredentials: true)
# to receive the HttpOnly refresh cookie, so we must echo a specific origin and
# allow credentials — a wildcard "*" origin is rejected by browsers for
# credentialed requests.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost",
]
CORS_ALLOW_CREDENTIALS = True

# Show full SQL queries in dev
LOGGING["loggers"]["django.db.backends"] = {
    "handlers": ["console"],
    "level": "DEBUG",
    "propagate": False,
}

# Celery: run tasks synchronously in tests (override per test if needed)
CELERY_TASK_ALWAYS_EAGER = False
