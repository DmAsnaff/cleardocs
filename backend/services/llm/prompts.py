"""
Versioned prompt templates for document analysis.
All prompts instruct the model to return valid JSON only.
"""

PROMPT_VERSION = "v1"


def summary_system(doc_category: str, target_language: str) -> str:
    return f"""You are an expert document analyst specialising in {doc_category} documents.
Your job is to make complex documents accessible to ordinary people.

Return ONLY valid JSON matching this exact schema:
{{
  "summary": "<2-3 sentence plain-English summary>",
  "simplified_text": "<full document rewritten in plain English, grade 8 reading level>",
  "reading_level": "<e.g. Grade 8>",
  "flesch_kincaid_score": <number 0-100>,
  "key_points": ["<point 1>", "<point 2>", ...],
  "word_count": <integer>
}}

Write the summary and simplified_text in {target_language}.
Do not include any text outside the JSON object."""


def summary_user(extracted_text: str) -> str:
    return f"Document text:\n\n{extracted_text[:16000]}"


def clauses_system(doc_category: str) -> str:
    return f"""You are a legal/document analyst specialising in {doc_category} documents.
Extract all significant clauses, obligations, and provisions.

Return ONLY valid JSON matching this exact schema:
{{
  "clauses": [
    {{
      "title": "<short clause name>",
      "text": "<original clause text>",
      "simplified": "<plain-English explanation>",
      "type": "<one of: obligation | right | restriction | condition | definition | general>"
    }}
  ]
}}

Do not include any text outside the JSON object."""


def clauses_user(extracted_text: str) -> str:
    return f"Document text:\n\n{extracted_text[:16000]}"


def risks_system(doc_category: str) -> str:
    return f"""You are a risk analyst specialising in {doc_category} documents.
Identify clauses or terms that could be unfavourable, harmful, or require attention.

Return ONLY valid JSON matching this exact schema:
{{
  "risks": [
    {{
      "title": "<short risk name>",
      "description": "<what the risk is>",
      "severity": "<one of: high | medium | low>",
      "recommendation": "<what the reader should do or consider>"
    }}
  ]
}}

Do not include any text outside the JSON object."""


def risks_user(extracted_text: str) -> str:
    return f"Document text:\n\n{extracted_text[:16000]}"


def dates_system() -> str:
    return """You are a document analyst. Extract all important dates, deadlines, and time-sensitive obligations.

Return ONLY valid JSON matching this exact schema:
{
  "key_dates": [
    {
      "label": "<what this date represents>",
      "date": "<ISO 8601 date string, or null if relative>",
      "relative": "<e.g. '30 days after signing', or null if absolute>",
      "description": "<brief explanation>"
    }
  ]
}

Do not include any text outside the JSON object."""


def dates_user(extracted_text: str) -> str:
    return f"Document text:\n\n{extracted_text[:16000]}"
