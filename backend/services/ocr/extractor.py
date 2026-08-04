import io
import logging

logger = logging.getLogger(__name__)


def extract_text(file_bytes: bytes, mime_type: str) -> str:
    """Route to the correct extractor based on MIME type."""
    if mime_type == "application/pdf":
        return _extract_pdf(file_bytes)
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _extract_docx(file_bytes)
    elif mime_type in ("image/jpeg", "image/png"):
        return _ocr_image(file_bytes)
    else:
        raise ValueError(f"Unsupported MIME type: {mime_type}")


def _extract_pdf(file_bytes: bytes) -> str:
    """
    Try native text extraction first (pdfplumber).
    Fall back to OCR if the PDF is scanned / image-only.
    """
    import pdfplumber

    text_parts = []
    page_count = 0

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)

    native_text = "\n".join(text_parts).strip()

    # Heuristic: if native extraction gives < 100 chars it's probably scanned
    if len(native_text) < 100:
        logger.info("pdf_ocr_fallback", extra={"page_count": page_count})
        return _ocr_pdf(file_bytes)

    return native_text


def _ocr_pdf(file_bytes: bytes) -> str:
    """Convert each PDF page to an image and OCR it."""
    try:
        from pdf2image import convert_from_bytes
        import pytesseract

        images = convert_from_bytes(file_bytes, dpi=200)
        parts = [pytesseract.image_to_string(img, lang="eng") for img in images]
        return "\n".join(parts).strip()
    except Exception as exc:
        logger.error("ocr_pdf_failed", extra={"error": str(exc)})
        raise


def _extract_docx(file_bytes: bytes) -> str:
    """Extract text from a Word document preserving paragraph structure."""
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _ocr_image(file_bytes: bytes) -> str:
    """OCR a raw image file (JPEG / PNG)."""
    import pytesseract
    from PIL import Image

    img = Image.open(io.BytesIO(file_bytes))
    return pytesseract.image_to_string(img, lang="eng").strip()
