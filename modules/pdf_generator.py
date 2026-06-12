from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def generate_pdf(article_text):
    filename = "article.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        spaceAfter=6,
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=20,
        spaceBefore=12,
        spaceAfter=4,
        textColor=colors.HexColor("#1a1a2e"),
    )

    story = []

    for line in article_text.split("\n"):
        stripped = line.strip()

        if not stripped:
            story.append(Spacer(1, 8))
            continue

        if stripped.startswith("## ") or stripped.startswith("### "):
            text = stripped.lstrip("#").strip()
            story.append(Paragraph(text, heading_style))
        elif stripped.startswith("# "):
            title_style = ParagraphStyle(
                "Title",
                parent=styles["Title"],
                fontSize=18,
                leading=24,
                spaceAfter=12,
                textColor=colors.HexColor("#1a1a2e"),
            )
            story.append(Paragraph(stripped.lstrip("#").strip(), title_style))
        else:
            safe = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe, body_style))

    doc.build(story)
    return filename