"""Root pytest configuration — fixtures here apply to the entire test suite,
including the app test packages under apps/*/tests/.
"""
import pytest


@pytest.fixture(autouse=True)
def clear_cache():
    """Reset the cache between every test.

    The login endpoint is rate-limited (5/minute via DRF's ScopedRateThrottle),
    and DRF stores throttle history in the default cache. Without clearing it
    between tests, login calls accumulate across the suite and later tests get
    throttled (HTTP 429), so no refresh-token cookie is set. Also resets token
    budget counters, which are cache-backed.
    """
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()
