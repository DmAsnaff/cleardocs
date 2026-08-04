from django.conf import settings
from .base import LLMProvider, LLMResponse

_MODEL = "claude-haiku-4-5-20251001"
_EMBED_DIM = 1536


class AnthropicProvider(LLMProvider):
    def __init__(self):
        import anthropic
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def complete(self, system: str, user: str, max_tokens: int = 2048) -> LLMResponse:
        response = self._client.messages.create(
            model=_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        content = response.content[0].text if response.content else ""
        usage = response.usage
        return LLMResponse(
            content=content,
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            model=_MODEL,
        )

    def stream_complete(self, system: str, user: str, max_tokens: int = 2048):
        with self._client.messages.stream(
            model=_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            for text in stream.text_stream:
                yield text

    def embed(self, text: str) -> list[float]:
        # Anthropic has no public embedding API — return zero vector as placeholder
        return [0.0] * _EMBED_DIM
