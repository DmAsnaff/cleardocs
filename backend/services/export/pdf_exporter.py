"""
PDF export: generates a simplified, human-readable PDF from a DocumentAnalysis
using ReportLab.
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem,
)

_SEVERITY_COLORS = {
    "high": colors.HexColor("#DC2626"),
    "medium": colors.HexColor("#D97706"),
    "low": colors.HexColor("#16A34A"),
}


def generate_pdf(doc, analysis) -> bytes:
    """
    Build a simplified PDF from a Document + DocumentAnalysis.
    Returns raw PDF bytes.
    """
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"Simplified — {doc.original_filename}",
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Title ──────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=4 * mm,
        textColor=colors.HexColor("#1E3A5F"),
    )
    story.append(Paragraph(f"Simplified Document", title_style))
    story.append(Paragraph(doc.original_filename, styles["Normal"]))
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E5E7EB")))
    story.append(Spacer(1, 4 * mm))

    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceAfter=3 * mm, textColor=colors.HexColor("#1E3A5F"))
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=15, spaceAfter=3 * mm)
    bullet = ParagraphStyle("Bullet", parent=styles["Normal"], fontSize=10, leading=14, leftIndent=6 * mm)

    # ── Summary ────────────────────────────────────────────────────────────
    if analysis.summary:
        story.append(Paragraph("Summary", h2))
        story.append(Paragraph(analysis.summary, body))
        story.append(Spacer(1, 3 * mm))

    # ── Reading level ──────────────────────────────────────────────────────
    if analysis.reading_level or analysis.flesch_kincaid_score is not None:
        meta_parts = []
        if analysis.reading_level:
            meta_parts.append(f"Reading level: {analysis.reading_level}")
        if analysis.flesch_kincaid_score is not None:
            meta_parts.append(f"Readability score: {analysis.flesch_kincaid_score:.0f}/100")
        story.append(Paragraph(" · ".join(meta_parts), styles["Italic"]))
        story.append(Spacer(1, 3 * mm))

    # ── Key points ─────────────────────────────────────────────────────────
    if analysis.key_points:
        story.append(Paragraph("Key Points", h2))
        items = [ListItem(Paragraph(pt, bullet), leftIndent=12) for pt in analysis.key_points]
        story.append(ListFlowable(items, bulletType="bullet", start="•"))
        story.append(Spacer(1, 3 * mm))

    # ── Simplified text ────────────────────────────────────────────────────
    if analysis.simplified_text:
        story.append(Paragraph("Plain-English Version", h2))
        for para in analysis.simplified_text.split("\n\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(para, body))

    # ── Clauses ────────────────────────────────────────────────────────────
    if analysis.clauses:
        story.append(Spacer(1, 4 * mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph("Clauses & Obligations", h2))
        for clause in analysis.clauses:
            title = clause.get("title", "")
            simplified = clause.get("simplified", "")
            ctype = clause.get("type", "general").capitalize()
            if title:
                story.append(Paragraph(f"<b>{title}</b> <font size='8' color='#6B7280'>[{ctype}]</font>", body))
            if simplified:
                story.append(Paragraph(simplified, bullet))
            story.append(Spacer(1, 2 * mm))

    # ── Risks ──────────────────────────────────────────────────────────────
    if analysis.risks:
        story.append(Spacer(1, 4 * mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph("Risks & Flags", h2))
        for risk in analysis.risks:
            severity = risk.get("severity", "low")
            sev_color = _SEVERITY_COLORS.get(severity, colors.black)
            title_str = risk.get("title", "")
            desc = risk.get("description", "")
            rec = risk.get("recommendation", "")
            if title_str:
                sev_label = severity.upper()
                story.append(Paragraph(
                    f"<b>{title_str}</b> <font color='#{_hex(sev_color)}' size='8'>[{sev_label}]</font>",
                    body,
                ))
            if desc:
                story.append(Paragraph(desc, bullet))
            if rec:
                story.append(Paragraph(f"<i>Recommendation: {rec}</i>", bullet))
            story.append(Spacer(1, 2 * mm))

    # ── Key dates ─────────────────────────────────────────────────────────
    if analysis.key_dates:
        story.append(Spacer(1, 4 * mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph("Important Dates & Deadlines", h2))
        for kd in analysis.key_dates:
            label = kd.get("label", "")
            date_str = kd.get("date") or kd.get("relative") or "—"
            desc = kd.get("description", "")
            story.append(Paragraph(f"<b>{label}</b>: {date_str}", body))
            if desc:
                story.append(Paragraph(desc, bullet))
            story.append(Spacer(1, 1.5 * mm))

    pdf.build(story)
    return buffer.getvalue()


def _hex(color) -> str:
    """Convert reportlab Color to 6-char hex string (no #)."""
    r, g, b = int(color.red * 255), int(color.green * 255), int(color.blue * 255)
    return f"{r:02X}{g:02X}{b:02X}"
