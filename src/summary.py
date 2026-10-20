from __future__ import annotations

import pandas as pd

from src.metrics import calculate_brand_health, get_risk_status, top_negative_aspect

RECOMMENDATIONS = {
    "delivery": "Publish a proactive delivery/logistics update and respond to delayed-order complaints.",
    "price": "Clarify value proposition, offer bundles/discounts, and address pricing objections.",
    "quality": "Share quality-control details and replace defective units quickly.",
    "support": "Escalate unresolved support tickets and publicly acknowledge response delays.",
    "packaging": "Improve packaging visuals and address damaged-in-transit reports.",
    "product": "Highlight product benefits and collect verified buyer reviews.",
    "service": "Train frontline teams and create a fast-track complaint resolution SOP.",
    "content": "Adjust creative tone, reduce overt promotion, and respond to audience feedback.",
    "influencer": "Vet creator authenticity and disclose partnerships clearly.",
    "brand": "Monitor brand sentiment and prepare a holding statement if negativity rises.",
}

DEFAULT_RECOMMENDATION = "Monitor comment trends and respond to recurring complaints with clear, empathetic messaging."


def generate_executive_summary(df: pd.DataFrame, metadata: dict | None = None) -> str:
    if df.empty:
        return "No comments available to summarize. Paste an Instagram URL, upload CSV, or run demo data."

    metadata = metadata or {}
    total = len(df)

    positive_pct = float((df["sentiment"] == "positive").mean() * 100) if "sentiment" in df else 0.0
    neutral_pct = float((df["sentiment"] == "neutral").mean() * 100) if "sentiment" in df else 0.0
    negative_pct = float((df["sentiment"] == "negative").mean() * 100) if "sentiment" in df else 0.0
    toxic_pct = float(df["is_toxic"].mean() * 100) if "is_toxic" in df else 0.0

    health = calculate_brand_health(df)
    risk = get_risk_status(df)

    if "emotion" in df and not df["emotion"].empty:
        top_emotion = df["emotion"].value_counts().index[0]
    else:
        top_emotion = "neutral"

    top_aspect = top_negative_aspect(df)
    recommendation = RECOMMENDATIONS.get(top_aspect, DEFAULT_RECOMMENDATION)

    source = metadata.get("source", "unknown")
    url = metadata.get("url")

    lines = [
        f"CommentSense AI analyzed {total} comments from source: {source}.",
    ]

    if url:
        lines.append(f"Input URL: {url}")

    lines.extend([
        f"Sentiment mix: {positive_pct:.1f}% positive, {neutral_pct:.1f}% neutral, {negative_pct:.1f}% negative.",
        f"Brand Health Score: {health}/100 ({risk['emoji']} {risk['label']}).",
        f"Dominant emotion: {top_emotion}. Toxic comments: {toxic_pct:.1f}%.",
    ])

    if top_aspect:
        lines.append(f"Top concern area: {top_aspect}.")

    lines.append(f"Recommended action: {recommendation}")

    return "\n".join(lines)