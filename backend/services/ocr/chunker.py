import re
from typing import Iterator

# Approx chars-per-token for estimation without tiktoken overhead
_CHARS_PER_TOKEN = 4
MAX_CHUNK_TOKENS = 3000
OVERLAP_TOKENS = 200
MAX_CHUNK_CHARS = MAX_CHUNK_TOKENS * _CHARS_PER_TOKEN
OVERLAP_CHARS = OVERLAP_TOKENS * _CHARS_PER_TOKEN

# Patterns that signal a new document section
_SECTION_PATTERN = re.compile(
    r"^(?:"
    r"\d+\.\s+[A-Z]"              # "1. Introduction"
    r"|[A-Z][A-Z\s]{4,}$"         # "DEFINITIONS"
    r"|Article\s+[IVX\d]"         # "Article IV"
    r"|Section\s+\d"              # "Section 3"
    r"|CLAUSE\s+\d"               # "CLAUSE 5"
    r")",
    re.MULTILINE,
)


def chunk_document(text: str) -> list[dict]:
    """
    Split a document into semantically meaningful chunks.

    Strategy (in priority order):
    1. Split on section headers (numbered sections, ALL CAPS headings, Article/Section markers)
    2. Split on paragraph boundaries (double newlines)
    3. If a block still exceeds MAX_CHUNK_CHARS, split on sentence boundaries

    Returns a list of dicts: [{"index": int, "text": str, "token_count": int}]
    """
    if not text or not text.strip():
        return []

    # Phase 1 — split by sections
    sections = _split_by_sections(text)

    # Phase 2 — split oversized sections by paragraph
    paragraphs: list[str] = []
    for section in sections:
        if len(section) > MAX_CHUNK_CHARS:
            paragraphs.extend(_split_by_paragraphs(section))
        else:
            paragraphs.append(section)

    # Phase 3 — split oversized paragraphs by sentence
    raw_chunks: list[str] = []
    for para in paragraphs:
        if len(para) > MAX_CHUNK_CHARS:
            raw_chunks.extend(_split_by_sentences(para))
        else:
            raw_chunks.append(para)

    # Remove empty strings
    raw_chunks = [c.strip() for c in raw_chunks if c.strip()]

    # Apply overlap: prepend the tail of the previous chunk
    chunks_with_overlap = list(_apply_overlap(raw_chunks))

    return [
        {
            "index": i,
            "text": chunk,
            "token_count": max(1, len(chunk) // _CHARS_PER_TOKEN),
        }
        for i, chunk in enumerate(chunks_with_overlap)
    ]


def _split_by_sections(text: str) -> list[str]:
    """Split text on section header patterns."""
    lines = text.split("\n")
    sections: list[str] = []
    current: list[str] = []

    for line in lines:
        if _SECTION_PATTERN.match(line.strip()) and current:
            sections.append("\n".join(current))
            current = [line]
        else:
            current.append(line)

    if current:
        sections.append("\n".join(current))

    return [s for s in sections if s.strip()]


def _split_by_paragraphs(text: str) -> list[str]:
    """Split on blank lines (double newline)."""
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def _split_by_sentences(text: str) -> list[str]:
    """Split into sentence groups that fit within MAX_CHUNK_CHARS."""
    # Simple sentence splitter: split on ". " / "? " / "! "
    sentences = re.split(r"(?<=[.?!])\s+", text)
    chunks: list[str] = []
    current_parts: list[str] = []
    current_len = 0

    for sentence in sentences:
        if current_len + len(sentence) > MAX_CHUNK_CHARS and current_parts:
            chunks.append(" ".join(current_parts))
            current_parts = []
            current_len = 0
        current_parts.append(sentence)
        current_len += len(sentence)

    if current_parts:
        chunks.append(" ".join(current_parts))

    return chunks


def _apply_overlap(chunks: list[str]) -> Iterator[str]:
    """Prepend the last OVERLAP_CHARS of the previous chunk for context continuity."""
    for i, chunk in enumerate(chunks):
        if i == 0:
            yield chunk
        else:
            tail = chunks[i - 1][-OVERLAP_CHARS:]
            yield tail + "\n\n" + chunk
