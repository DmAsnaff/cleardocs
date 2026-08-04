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

# Allow all CORS origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Show full SQL queries in dev
LOGGING["loggers"]["django.db.backends"] = {
    "handlers": ["console"],
    "level": "DEBUG",
    "propagate": False,
}

# Celery: run tasks synchronously in tests (override per test if needed)
CELERY_TASK_ALWAYS_EAGER = False
