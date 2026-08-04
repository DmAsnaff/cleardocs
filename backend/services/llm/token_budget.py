"""
Token budget enforcement.
- Per-document limit: MAX_TOKENS_PER_DOCUMENT (default 100k)
- Per-user-per-day limit: MAX_TOKENS_PER_USER_PER_DAY (default 500k)

Uses Django's Redis cache for the daily user counter.
"""
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

_DOC_LIMIT = getattr(settings, "MAX_TOKENS_PER_DOCUMENT", 100_000)
_USER_DAY_LIMIT = getattr(settings, "MAX_TOKENS_PER_USER_PER_DAY", 500_000)
_TTL = 86_400  # 24 hours in seconds


class TokenBudgetExceeded(Exception):
    pass


def check_document_budget(tokens_so_far: int, tokens_to_add: int) -> None:
    """Raise TokenBudgetExceeded if adding tokens_to_add would exceed the per-document limit."""
    if tokens_so_far + tokens_to_add > _DOC_LIMIT:
        raise TokenBudgetExceeded(
            f"Document token budget exceeded: {tokens_so_far + tokens_to_add} > {_DOC_LIMIT}"
        )


def get_user_tokens_today(user_id: str) -> int:
    return cache.get(_user_key(user_id), 0)


def add_user_tokens(user_id: str, tokens: int) -> int:
    """Increment the user's daily token count. Returns the new total."""
    key = _user_key(user_id)
    try:
        new_total = cache.incr(key, tokens)
    except ValueError:
        # Key doesn't exist — set it with TTL
        cache.set(key, tokens, timeout=_TTL)
        new_total = tokens
    return new_total


def check_user_daily_budget(user_id: str, tokens_to_add: int) -> None:
    """Raise TokenBudgetExceeded if the user would exceed their daily limit."""
    current = get_user_tokens_today(user_id)
    if current + tokens_to_add > _USER_DAY_LIMIT:
        raise TokenBudgetExceeded(
            f"Daily token budget exceeded for user {user_id}: "
            f"{current + tokens_to_add} > {_USER_DAY_LIMIT}"
        )


def _user_key(user_id: str) -> str:
    from django.utils import timezone
    today = timezone.now().strftime("%Y-%m-%d")
    return f"token_budget:{user_id}:{today}"
