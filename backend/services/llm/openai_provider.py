from django.conf import settings
from .base import LLMProvider, LLMResponse

_EMBED_MODEL = "text-embedding-3-small"


class OpenAIProvider(LLMProvider):
    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.OPENAI_MODEL

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
        response = self._client.embeddings.create(model=_EMBED_MODEL, input=text)
        return response.data[0].embedding
