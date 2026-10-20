from __future__ import annotations

import json
import time
from pathlib import Path

CACHE_DIR = Path(".cache")
CACHE_FILE = CACHE_DIR / "commentsense_cache.json"


def _load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_cached_comments(key: str, ttl_seconds: int = 1800) -> list | None:
    cache = _load_cache()
    item = cache.get(key)
    if not item:
        return None

    cached_at = item.get("cached_at", 0)
    comments = item.get("comments")

    if not isinstance(comments, list):
        return None

    if time.time() - float(cached_at) > ttl_seconds:
        return None

    return comments


def set_cached_comments(key: str, comments: list) -> None:
    cache = _load_cache()
    cache[key] = {
        "cached_at": time.time(),
        "comments": comments,
    }
    _save_cache(cache)


def clear_cache() -> None:
    if CACHE_FILE.exists():
        try:
            CACHE_FILE.unlink()
        except Exception:
            pass