import pytest
from django.conf import settings


@pytest.fixture(autouse=True)
def use_test_settings(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CLAMAV_ENABLED = False
    settings.LLM_PROVIDER = "mock"
