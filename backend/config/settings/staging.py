from .base import *  # noqa

DEBUG = False

ALLOWED_HOSTS = [os.environ.get("ALLOWED_HOST", "staging.cleardocs.app")]

CORS_ALLOWED_ORIGINS = [
    "https://staging.cleardocs.app",
]

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

CLAMAV_ENABLED = True

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
