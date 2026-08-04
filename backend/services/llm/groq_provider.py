import logging
from django.conf import settings
from .base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

# Groq doesn't offer a native embedding endpoint — use a lightweight local model
# or fall back to a small OpenAI-compatible embedding. For dev we use a stub.
_EMBED_DIM = 1536


class GroqProvider(LLMProvider):
    def __init__(self):
        from groq import Groq
        self._client = Groq(api_key=settings.GROQ_API_KEY)
        self._model = settings.GROQ_MODEL

    def complete(self, system: str, user: str, max_tokens: int = 2048) -> LLMResponse:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        choice = response.choices[0]
        usage = response.usage
        return LLMResponse(
            content=choice.message.content or "",
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            model=self._model,
        )

    def stream_complete(self, system: str, user: str, max_tokens: int = 2048):
        stream = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def embed(self, text: str) -> list[float]:
        # Groq has no embedding API — return zero vector as placeholder
        # Replace with sentence-transformers or OpenAI embeddings if needed
        logger.debug("groq_embed_stub", extra={"chars": len(text)})
        return [0.0] * _EMBED_DIM
