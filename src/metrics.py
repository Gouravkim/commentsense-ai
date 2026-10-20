from __future__ import annotations

import pandas as pd


def _percentage(df: pd.DataFrame, column: str, value) -> float:
    if df.empty or column not in df.columns:
        return 0.0
    return float((df[column] == value).mean() * 100)


def calculate_brand_health(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0

    positive = (df["sentiment"] == "positive").mean() if "sentiment" in df else 0.0
    neutral = (df["sentiment"] == "neutral").mean() if "sentiment" in df else 0.0
    negative = (df["sentiment"] == "negative").mean() if "sentiment" in df else 0.0
    toxic = df["is_toxic"].mean() if "is_toxic" in df else 0.0

    joy = (df["emotion"] == "joy").mean() if "emotion" in df else 0.0
    anger = (df["emotion"] == "anger").mean() if "emotion" in df else 0.0
    sadness = (df["emotion"] == "sadness").mean() if "emotion" in df else 0.0

    score = (
        positive * 50
        + neutral * 20
        - negative * 10
        - toxic * 40
        + joy * 10
        - anger * 10
        - sadness * 5
    )

    return float(max(0.0, min(100.0, round(score, 1))))


def top_negative_aspect(df: pd.DataFrame) -> str | None:
    if df.empty or "aspects" not in df.columns:
        return None

    counts: dict[str, int] = {}

    for aspects in df["aspects"]:
        if not isinstance(aspects, dict):
            continue
        for aspect, info in aspects.items():
            if isinstance(info, dict) and info.get("sentiment") == "negative":
                counts[aspect] = counts.get(aspect, 0) + 1

    if not counts:
        return None

    return max(counts, key=counts.get)


def get_risk_status(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "level": "unknown",
            "label": "No Data",
            "emoji": "⚪",
            "reason": "No comments available.",
            "action": "Run demo or upload CSV.",
            "toxic_pct": 0.0,
            "negative_pct": 0.0,
            "anger_pct": 0.0,
        }

    toxic_pct = _percentage(df, "is_toxic", True)
    negative_pct = _percentage(df, "sentiment", "negative")
    anger_pct = _percentage(df, "emotion", "anger")

    reasons = []
    if toxic_pct > 20:
        reasons.append(f"Toxic comments at {toxic_pct:.1f}%")
    elif toxic_pct > 10:
        reasons.append(f"Elevated toxicity at {toxic_pct:.1f}%")
    elif toxic_pct > 5:
        reasons.append(f"Mild toxicity at {toxic_pct:.1f}%")

    if negative_pct > 50:
        reasons.append(f"Negative sentiment at {negative_pct:.1f}%")
    elif negative_pct > 35:
        reasons.append(f"High negative sentiment at {negative_pct:.1f}%")
    elif negative_pct > 20:
        reasons.append(f"Negative sentiment at {negative_pct:.1f}%")

    if anger_pct > 30:
        reasons.append(f"Anger emotion at {anger_pct:.1f}%")

    top_aspect = top_negative_aspect(df)
    if top_aspect:
        reasons.append(f"Top concern area: {top_aspect}")

    if not reasons:
        reasons.append("Metrics are within normal range.")

    if toxic_pct > 20 or negative_pct > 50 or anger_pct > 30:
        level = "critical"
        label = "Critical"
        emoji = "🔴"
        action = "Activate crisis response: pause promotional posts, acknowledge issues, and respond to top complaints publicly."
    elif toxic_pct > 10 or negative_pct > 35:
        level = "warning"
        label = "Warning"
        emoji = "🟠"
        action = "Investigate top negative aspects and prepare a clarifying response before sentiment worsens."
    elif toxic_pct > 5 or negative_pct > 20:
        level = "monitor"
        label = "Monitor"
        emoji = "🟡"
        action = "Track comment trend for next 24 hours and reply to recurring complaints."
    else:
        level = "healthy"
        label = "Healthy"
        emoji = "🟢"
        action = "Continue normal engagement. Highlight positive comments and maintain response speed."

    return {
        "level": level,
        "label": label,
        "emoji": emoji,
        "reason": " | ".join(reasons),
        "action": action,
        "toxic_pct": round(toxic_pct, 1),
        "negative_pct": round(negative_pct, 1),
        "anger_pct": round(anger_pct, 1),
    }