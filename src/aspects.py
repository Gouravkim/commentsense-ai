from __future__ import annotations

import re

ASPECT_KEYWORDS = {
    "delivery": [
        "delivery", "deliver", "shipping", "ship", "courier", "late", "delay",
        "tracking", "track", "dispatch", "arrived", "arrival", "der", "lat"
    ],
    "price": [
        "price", "pricing", "cost", "expensive", "cheap", "overpriced",
        "value", "worth", "money", "paisa", "rate", "mehnga", "discount"
    ],
    "quality": [
        "quality", "material", "fabric", "build", "damaged", "damage",
        "broken", "defective", "faulty", "mast", "solid", "premium",
        "average", "kharab"
    ],
    "support": [
        "support", "customer", "care", "refund", "help", "reply",
        "response", "agent", "team", "escalation", "complaint"
    ],
    "packaging": [
        "packaging", "package", "packed", "box", "cover", "wrapped",
        "bubble", "sealed"
    ],
    "product": [
        "product", "item", "piece", "thing", "purchase", "bought",
        "order", "unit"
    ],
    "service": [
        "service", "experience", "staff", "team", "assistance",
        "after sales", "aftersales"
    ],
    "content": [
        "video", "reel", "content", "edit", "editing", "song",
        "music", "caption", "post", "creative"
    ],
    "influencer": [
        "influencer", "promotion", "promoting", "ad", "ads",
        "sponsor", "sponsored", "paid", "collab", "creator"
    ],
    "brand": [
        "brand", "company", "nike", "adidas", "zomato", "swiggy",
        "boAt", "noise", "apple", "samsung"
    ],
}

POS_WORDS = {
    "good", "great", "awesome", "amazing", "love", "best", "happy",
    "excellent", "superb", "fast", "worth", "recommend", "beautiful",
    "perfect", "nice", "solid", "smooth", "helpful", "premium",
    "mast", "accha", "achha", "badhiya", "paisa vasool", "top class",
    "value for money", "impressed", "thank"
}

NEG_WORDS = {
    "bad", "worst", "hate", "terrible", "awful", "late", "delay",
    "damaged", "broken", "defective", "faulty", "expensive",
    "overpriced", "refund", "scam", "fake", "poor", "disappointed",
    "useless", "garbage", "trash", "cringe", "boring", "mushkil",
    "skip", "regret", "kharab", "ignore", "unresponsive", "painful",
    "confusing", "forced"
}

CLAUSE_SPLIT_RE = re.compile(r"\b(?:but|however|though|although|yet|still)\b|[;.\n]", re.IGNORECASE)


def _contains_any(text_lower: str, keywords: list[str]) -> list[str]:
    return [kw for kw in keywords if kw in text_lower]


def _clause_polarity(clause: str) -> str:
    clause_lower = clause.lower()
    pos = sum(1 for w in POS_WORDS if w in clause_lower)
    neg = sum(1 for w in NEG_WORDS if w in clause_lower)

    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def extract_aspects(text: str, overall_sentiment: str, overall_score: float) -> dict:
    """
    Very lightweight aspect-based sentiment for MVP.
    It detects aspect keywords and tries clause-level polarity.
    """
    if not text:
        return {}

    text_lower = text.lower()
    clauses = [c.strip() for c in CLAUSE_SPLIT_RE.split(text) if c and c.strip()]
    aspects = {}

    for aspect, keywords in ASPECT_KEYWORDS.items():
        matched = _contains_any(text_lower, keywords)
        if not matched:
            continue

        aspect_sentiment = overall_sentiment
        confidence = float(overall_score or 0.5)

        # Try to find a clause containing the aspect keyword
        for clause in clauses:
            clause_lower = clause.lower()
            if any(kw in clause_lower for kw in keywords):
                polarity = _clause_polarity(clause)
                if polarity != "neutral":
                    aspect_sentiment = polarity
                    confidence = 0.80
                break

        # If overall is neutral but clause has no polarity, keep neutral
        if aspect_sentiment == "neutral" and overall_sentiment != "neutral":
            aspect_sentiment = overall_sentiment
            confidence = float(overall_score or 0.5)

        aspects[aspect] = {
            "sentiment": aspect_sentiment,
            "keywords": matched[:5],
            "confidence": round(confidence, 3),
        }

    return aspects


def summarize_aspects(aspects: dict) -> str:
    if not aspects:
        return ""

    # Negative first for visibility
    items = sorted(
        aspects.items(),
        key=lambda x: (
            0 if x[1].get("sentiment") == "negative" else
            1 if x[1].get("sentiment") == "positive" else
            2
        )
    )

    return ", ".join(f"{aspect}: {info.get('sentiment', 'neutral')}" for aspect, info in items)


def aspect_flags(aspects: dict) -> list[str]:
    flags = []
    for aspect, info in (aspects or {}).items():
        sentiment = info.get("sentiment", "neutral")
        if sentiment in {"negative", "toxic"}:
            flags.append(f"{aspect}_{sentiment}")
    return flags