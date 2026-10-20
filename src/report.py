from __future__ import annotations

import json
from datetime import datetime, timezone
from io import BytesIO
from xml.sax.saxutils import escape

import pandas as pd

from src.metrics import calculate_brand_health, get_risk_status


def export_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def export_json(df: pd.DataFrame, metadata: dict | None = None, summary: str = "") -> bytes:
    metadata = metadata or {}

    payload = {
        "metadata": metadata,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "executive_summary": summary,
        "aggregate": {
            "total_comments": int(len(df)),
            "brand_health_score": calculate_brand_health(df),
            "risk_status": get_risk_status(df),
            "sentiment_distribution": df["sentiment"].value_counts().to_dict() if "sentiment" in df else {},
            "emotion_distribution": df["emotion"].value_counts().to_dict() if "emotion" in df else {},
            "toxic_comments": int(df["is_toxic"].sum()) if "is_toxic" in df else 0,
        },
        "comments": df.to_dict(orient="records"),
    }

    return json.dumps(payload, indent=2, default=str).encode("utf-8")


def _truncate(text: str, limit: int = 90) -> str:
    text = str(text or "")
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def export_pdf_report(df: pd.DataFrame, metadata: dict | None = None, summary: str = "") -> bytes | None:
    """
    Optional PDF report. Returns None if reportlab is unavailable.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except Exception:
        return None

    metadata = metadata or {}
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("CommentSense AI Report", styles["Title"]))
    story.append(Spacer(1, 8))

    meta_lines = [
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"Source: {metadata.get('source', 'unknown')}",
    ]

    if metadata.get("url"):
        meta_lines.append(f"URL: {escape(str(metadata['url']))}")
    if metadata.get("dataset"):
        meta_lines.append(f"Demo dataset: {escape(str(metadata['dataset']))}")
    if metadata.get("filename"):
        meta_lines.append(f"Uploaded file: {escape(str(metadata['filename']))}")

    story.append(Paragraph("<br/>".join(meta_lines), styles["Normal"]))
    story.append(Spacer(1, 12))

    health = calculate_brand_health(df)
    risk = get_risk_status(df)

    story.append(Paragraph("Executive Summary", styles["Heading2"]))
    summary_html = escape(summary).replace("\n", "<br/>")
    story.append(Paragraph(summary_html, styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Key Metrics", styles["Heading2"]))
    metric_data = [
        ["Metric", "Value"],
        ["Total Comments", str(len(df))],
        ["Brand Health Score", f"{health}/100"],
        ["Risk Status", f"{risk['emoji']} {risk['label']}"],
        ["Toxic %", f"{risk['toxic_pct']}%"],
        ["Negative %", f"{risk['negative_pct']}%"],
        ["Anger %", f"{risk['anger_pct']}%"],
    ]

    metric_table = Table(metric_data, colWidths=[70 * mm, 90 * mm])
    metric_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(metric_table)
    story.append(Spacer(1, 14))

    if not df.empty and "is_toxic" in df.columns:
        toxic_df = df[df["is_toxic"]].sort_values("toxicity_score", ascending=False).head(10)
        if not toxic_df.empty:
            story.append(Paragraph("Top Toxic Comments", styles["Heading2"]))
            rows = [["Comment", "Toxicity Label", "Score"]]
            for _, row in toxic_df.iterrows():
                rows.append([
                    escape(_truncate(row.get("text", ""), 80)),
                    escape(str(row.get("toxicity_label", ""))),
                    f"{float(row.get('toxicity_score', 0) or 0):.2f}",
                ])

            toxic_table = Table(rows, colWidths=[95 * mm, 40 * mm, 20 * mm])
            toxic_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7f1d1d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]))
            story.append(toxic_table)

    doc.build(story)
    return buffer.getvalue()