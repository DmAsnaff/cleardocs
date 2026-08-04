from .base import *  # noqa

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "test_cleardocs"),
        "USER": os.environ.get("POSTGRES_USER", "cleardocs"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "testpassword"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Use an in-process cache for tests — hermetic (no Redis) and isolated so
# throttle state does not leak between tests. conftest clears it per test.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CLAMAV_ENABLED = False

DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
MEDIA_ROOT = BASE_DIR / "test_media"

LLM_PROVIDER = "mock"
