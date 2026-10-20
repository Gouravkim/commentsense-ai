from __future__ import annotations

import hashlib
import re
import uuid
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
SHORTCODE_RE = re.compile(r"/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)")


def extract_shortcode(url: str | None) -> str | None:
    """
    Extract Instagram shortcode from:
    - https://www.instagram.com/p/CODE/
    - https://www.instagram.com/reel/CODE/
    - https://www.instagram.com/tv/CODE/
    - https://instagram.com/p/CODE?utm_source=...
    """
    if not url:
        return None

    url = url.strip()
    match = SHORTCODE_RE.search(url)
    if match:
        return match.group(1)

    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]

    if parts and parts[0] in {"p", "reel", "reels", "tv"} and len(parts) >= 2:
        return parts[1]

    if parts:
        return parts[-1]

    return None


def clean_text(text: str | None) -> str:
    if text is None:
        return ""
    text = str(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def redact_pii(text: str | None) -> str:
    if text is None:
        return ""

    text = str(text)
    text = EMAIL_RE.sub("[EMAIL_REDACTED]", text)
    text = PHONE_RE.sub("[PHONE_REDACTED]", text)
    text = URL_RE.sub("[LINK_REDACTED]", text)
    return text


def prepare_text(text: str | None) -> str:
    return clean_text(redact_pii(text))


def hash_username(username: str | None) -> str | None:
    if not username:
        return None
    return hashlib.sha256(str(username).encode("utf-8")).hexdigest()[:16]


def _safe_int(value, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def normalize_comment(item, source: str = "unknown", shortcode: str | None = None) -> dict:
    """
    Normalize comment from str, dict, or object into standard schema.
    """
    meta = {}
    text = ""
    username = None
    timestamp = None
    likes = 0

    if isinstance(item, str):
        text = item
    elif isinstance(item, dict):
        meta = dict(item)
        text = meta.get("text") or meta.get("comment") or meta.get("comment_text") or ""
        username = meta.get("username") or meta.get("user") or meta.get("from")
        timestamp = meta.get("timestamp") or meta.get("created_at") or meta.get("time")
        likes = _safe_int(meta.get("likes") or meta.get("like_count") or meta.get("likes_count"), 0)
        source = meta.get("source") or source
        shortcode = shortcode or meta.get("post_shortcode") or meta.get("shortcode")
    else:
        text = getattr(item, "text", None) or getattr(item, "comment", None) or ""
        username = getattr(item, "username", None) or getattr(item, "user", None)
        timestamp = getattr(item, "timestamp", None) or getattr(item, "created_at", None)
        likes = _safe_int(getattr(item, "likes", None) or getattr(item, "like_count", None), 0)

    text = prepare_text(text)

    return {
        "comment_id": meta.get("comment_id") or str(uuid.uuid4()),
        "text": text,
        "username_hash": hash_username(username),
        "timestamp": timestamp,
        "likes": likes,
        "source": source,
        "post_shortcode": shortcode,
    }