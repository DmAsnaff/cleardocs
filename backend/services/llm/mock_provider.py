"""Mock LLM provider for tests — returns deterministic JSON responses."""
import json
from .base import LLMProvider, LLMResponse

_EMBED_DIM = 1536


class MockProvider(LLMProvider):
    def complete(self, system: str, user: str, max_tokens: int = 2048) -> LLMResponse:
        # Match on the distinctive output-schema key each prompt requests.
        # These keys are disjoint across prompts, so order is unambiguous —
        # unlike fuzzy words such as "simplif", which appears in both the
        # summary and clause prompts.
        s = system.lower()
        if "clauses" in s:
            content = json.dumps({"clauses": [
                {"title": "Test Clause", "text": "Original text.", "simplified": "Simple text.", "type": "general"},
            ]})
        elif "risks" in s:
            content = json.dumps({"risks": [
                {"title": "Test Risk", "description": "A risk.", "severity": "low", "recommendation": "Review it."},
            ]})
        elif "key_dates" in s or "deadline" in s:
            content = json.dumps({"key_dates": [
                {"label": "Effective Date", "date": "2025-01-01", "description": "Contract starts."},
            ]})
        elif "summary" in s or "simplif" in s:
            content = json.dumps({
                "summary": "This is a test document summary.",
                "simplified_text": "This document says some things in plain language.",
                "reading_level": "Grade 8",
                "flesch_kincaid_score": 65.0,
                "key_points": ["Point one.", "Point two."],
                "word_count": 42,
            })
        else:
            content = json.dumps({"result": "mock"})

        return LLMResponse(
            content=content,
            prompt_tokens=100,
            completion_tokens=50,
            model="mock",
        )

    def stream_complete(self, system: str, user: str, max_tokens: int = 2048):
        words = "This is a mock streaming response from the AI assistant. ".split()
        for word in words:
            yield word + " "

    def embed(self, text: str) -> list[float]:
        return [0.1] * _EMBED_DIM
