from django.conf import settings
from .base import LLMProvider

_provider_instance: LLMProvider | None = None


def reset_provider() -> None:
    """Reset the cached provider — used in tests when LLM_PROVIDER changes."""
    global _provider_instance
    _provider_instance = None


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider singleton."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = _build_provider()
    return _provider_instance


def _build_provider() -> LLMProvider:
    provider_name = getattr(settings, "LLM_PROVIDER", "openai").lower()

    if provider_name == "groq":
        from .groq_provider import GroqProvider
        return GroqProvider()
    elif provider_name == "anthropic":
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    elif provider_name == "mock":
        from .mock_provider import MockProvider
        return MockProvider()
    else:
        from .openai_provider import OpenAIProvider
        return OpenAIProvider()
