"""Abstract base class for LLM providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int
    completion_tokens: int
    model: str

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, system: str, user: str, max_tokens: int = 2048) -> LLMResponse:
        """Send a chat completion request and return the full response."""
        ...

    @abstractmethod
    def stream_complete(self, system: str, user: str, max_tokens: int = 2048) -> Iterator[str]:
        """Yield content chunks as they arrive (for streaming chat responses)."""
        ...

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Return an embedding vector for the given text."""
        ...
