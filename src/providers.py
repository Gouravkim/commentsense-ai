from __future__ import annotations

import csv
import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.utils import normalize_comment

DATA_DIR = Path("data")

POSITIVE_TEMPLATES = [
    "This is amazing!",
    "Love the quality",
    "Best purchase ever",
    "Really happy with this",
    "Great content 🔥",
    "Superb service",
    "Exactly what I wanted",
    "Highly recommend",
    "Beautiful design",
    "Fast delivery and great packaging",
    "Value for money",
    "So impressed",
    "This made my day",
    "Excellent work",
    "Keep it up",
    "Product quality is solid",
    "Customer support was helpful",
    "Reel editing is top class",
]

NEGATIVE_TEMPLATES = [
    "Delivery was very late",
    "Product got damaged",
    "Not worth the price",
    "Customer support did not reply",
    "Packaging was terrible",
    "Expected better quality",
    "Refund process is painful",
    "Worst experience",
    "Disappointed with the service",
    "Too expensive for what it is",
    "Tracking was confusing",
    "Item was defective",
    "Poor after sales support",
    "Regret buying this",
    "Content feels forced",
    "Shipping took forever",
    "Quality dropped recently",
    "Support team is unresponsive",
]

TOXIC_TEMPLATES = [
    "This is garbage, shut up",
    "You are an idiot for promoting this",
    "Total scam, don't buy",
    "Fake promotion, so cringe",
    "Worst brand ever, hate this",
    "Stop posting rubbish",
    "This ad is disgusting",
    "You people are useless",
    "Trash product, trash team",
    "Don't trust this nonsense",
    "Absolutely pathetic content",
    "This is insulting to customers",
]

HINGLISH_TEMPLATES = [
    "Product mast hai but delivery late thi",
    "Paisa vasool quality hai",
    "Customer support ne reply nahi kiya",
    "Content boring hai yaar",
    "Packaging acchi thi, item average",
    "Rate too high hai, skip kar diya",
    "Love this reel, super edit",
    "Cringe promotion lag raha hai",
    "Refund milna mushkil hai",
    "Value for money hai bhai",
    "Delivery fast thi, product okay",
    "Support worst hai, ignore kar rahe hain",
    "Quality previous se kharab hai",
    "Ad itna fake lag raha hai",
]

NEUTRAL_TEMPLATES = [
    "Just saw this",
    "Waiting for review",
    "How much?",
    "Link please",
    "Following",
    "Not sure about this",
    "Maybe later",
    "Interesting",
    "Need more details",
    "Will check",
]

TEMPLATES = {
    "positive": POSITIVE_TEMPLATES,
    "negative": NEGATIVE_TEMPLATES,
    "toxic": TOXIC_TEMPLATES,
    "hinglish": HINGLISH_TEMPLATES,
    "neutral": NEUTRAL_TEMPLATES,
}

PROFILES = {
    "demo_healthy.csv": {
        "positive": 0.72,
        "neutral": 0.15,
        "hinglish": 0.08,
        "negative": 0.04,
        "toxic": 0.01,
    },
    "demo_mixed.csv": {
        "positive": 0.42,
        "neutral": 0.10,
        "negative": 0.25,
        "toxic": 0.08,
        "hinglish": 0.15,
    },
    "demo_crisis.csv": {
        "positive": 0.12,
        "neutral": 0.05,
        "negative": 0.45,
        "toxic": 0.25,
        "hinglish": 0.13,
    },
    "demo_hinglish.csv": {
        "positive": 0.25,
        "neutral": 0.05,
        "negative": 0.30,
        "toxic": 0.10,
        "hinglish": 0.30,
    },
}


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["comment", "username", "timestamp", "likes", "source"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_demo_csv(filename: str, count: int = 120, profile: str = "demo_mixed.csv", seed: int = 42) -> Path:
    rng = random.Random(seed)
    weights = PROFILES.get(profile, PROFILES["demo_mixed.csv"])
    categories = list(weights.keys())
    category_weights = list(weights.values())

    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=24)

    rows = []
    for i in range(count):
        category = rng.choices(categories, weights=category_weights)[0]
        template = rng.choice(TEMPLATES.get(category, NEUTRAL_TEMPLATES))

        # Small variation to reduce exact duplicates
        if rng.random() < 0.25:
            template = template + " " + rng.choice(["", "😅", "👍", "", "", "⚠️", "🙏"]).strip()

        timestamp = (start + timedelta(seconds=rng.randint(0, 86400))).isoformat()
        likes = rng.randint(0, 250)
        if category == "toxic":
            likes = rng.randint(0, 80)
        elif category == "positive":
            likes = rng.randint(5, 500)

        rows.append({
            "comment": template.strip(),
            "username": f"user_{i+1}",
            "timestamp": timestamp,
            "likes": likes,
            "source": "demo",
        })

    path = DATA_DIR / filename
    _write_csv(path, rows)
    return path


def ensure_demo_file(filename: str, count: int = 120, profile: str | None = None) -> Path:
    profile = profile or filename
    if profile not in PROFILES:
        profile = "demo_mixed.csv"

    path = DATA_DIR / filename
    if not path.exists() or path.stat().st_size == 0:
        generate_demo_csv(filename=filename, count=count, profile=profile)
    return path


def load_demo(filename: str = "demo_mixed.csv", count: int = 120) -> list[dict]:
    path = ensure_demo_file(filename=filename, count=count, profile=filename)
    comments = []

    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            comments.append(normalize_comment(row, source="demo"))

    return comments


def load_csv_path(path: str | Path) -> list[dict]:
    path = Path(path)
    comments = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            comments.append(normalize_comment(row, source="csv"))
    return comments


def load_csv_dataframe(df) -> list[dict]:
    """
    Accept a pandas DataFrame and normalize it.
    Required column: comment / text / comments / comment_text
    Optional columns: username, user, timestamp, created_at, likes, like_count, source
    """
    if df is None or len(df) == 0:
        return []

    comment_col = None
    for col in df.columns:
        if str(col).strip().lower() in {"comment", "text", "comments", "comment_text"}:
            comment_col = col
            break

    if not comment_col:
        raise ValueError("CSV must contain a column named 'comment' or 'text'.")

    comments = []
    for row in df.to_dict(orient="records"):
        text = row.get(comment_col)
        if text is None:
            continue
        if str(text).strip().lower() in {"", "nan", "none"}:
            continue

        normalized = normalize_comment({
            "text": text,
            "username": row.get("username") or row.get("user") or row.get("from"),
            "timestamp": row.get("timestamp") or row.get("created_at") or row.get("time"),
            "likes": row.get("likes") or row.get("like_count") or row.get("likes_count"),
            "source": row.get("source") or "csv",
        }, source="csv")

        if normalized["text"]:
            comments.append(normalized)

    return comments


def _extract_texts(obj, out: list | None = None, seen: set | None = None, depth: int = 0) -> list[str]:
    """
    Recursively extract comment text from instagrapi/API responses.
    Handles dict, list, object with .text, generators, etc.
    """
    if out is None:
        out = []
    if seen is None:
        seen = set()

    if depth > 8 or obj is None:
        return out

    if isinstance(obj, str):
        text = obj.strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
        return out

    if isinstance(obj, dict):
        for key in ("text", "message", "comment", "comment_text"):
            value = obj.get(key)
            if isinstance(value, str):
                text = value.strip()
                if text and text not in seen:
                    seen.add(text)
                    out.append(text)

        for value in obj.values():
            _extract_texts(value, out, seen, depth + 1)

        return out

    if isinstance(obj, (list, tuple, set)):
        for value in obj:
            _extract_texts(value, out, seen, depth + 1)
        return out

    # Generators / custom iterables
    if hasattr(obj, "__iter__") and not isinstance(obj, (bytes, bytearray)):
        try:
            for value in obj:
                _extract_texts(value, out, seen, depth + 1)
            return out
        except Exception:
            pass

    # Objects with attributes
    for attr in ("text", "message", "comment"):
        value = getattr(obj, attr, None)
        if isinstance(value, str):
            text = value.strip()
            if text and text not in seen:
                seen.add(text)
                out.append(text)

    return out


def fetch_instagrapi_comments(shortcode: str, amount: int = 100) -> list[dict] | None:
    """
    Best-effort public comment fetch using instagrapi.
    This is unofficial and may fail depending on Instagram changes.
    """
    try:
        from instagrapi import Client
    except Exception:
        return None

    try:
        cl = Client()
        cl.delay_range = [2, 5]
    except Exception:
        return None

    method_names = [
        "media_comments_public_gql",
        "media_comments_public",
        "comments_media_public",
        "media_comments",
    ]

    for method_name in method_names:
        method = getattr(cl, method_name, None)
        if not callable(method):
            continue

        call_variants = [
            ((shortcode,), {"amount": amount}),
            ((shortcode, amount), {}),
            ((shortcode,), {}),
        ]

        for args, kwargs in call_variants:
            try:
                response = method(*args, **kwargs)
                texts = _extract_texts(response)
                if texts:
                    return [
                        normalize_comment({"text": t, "source": "instagrapi", "post_shortcode": shortcode})
                        for t in texts[:amount]
                    ]
            except TypeError:
                continue
            except Exception:
                continue

    return None


def fetch_official_api_comments(shortcode: str, amount: int = 100) -> list[dict] | None:
    """
    Optional authorized/local JSON provider.

    Set IG_AUTHORIZED_COMMENTS_FILE=path/to/comments.json

    JSON format examples:
    1) {
         "CjPUjEvDKT4": [
           {"text": "Great product", "username": "user1", "likes": 10}
         ]
       }

    2) [
         {"text": "Great product", "username": "user1", "likes": 10}
       ]
    """
    path = os.getenv("IG_AUTHORIZED_COMMENTS_FILE")
    if not path:
        return None

    file_path = Path(path)
    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None

    if isinstance(data, dict):
        scoped = data.get(shortcode) or data.get("comments") or data
    else:
        scoped = data

    texts = _extract_texts(scoped)
    if not texts:
        # Try preserving dict records if they already contain text
        records = []
        if isinstance(scoped, list):
            for item in scoped[:amount]:
                records.append(normalize_comment(item, source="official_api", shortcode=shortcode))
        return records or None

    return [
        normalize_comment({"text": t, "source": "official_api", "post_shortcode": shortcode})
        for t in texts[:amount]
    ]
# ---------- AUTHENTICATED (REAL COMMENTS) ----------

def _get_auth_client():
    """session.json (library card) se authenticated client banao."""
    try:
        from instagrapi import Client
    except Exception:
        return None

    cl = Client()
    cl.delay_range = [1, 2]

    # 1) Pehle session file try karo (password ki zaroorat nahi)
    sess = Path(os.getenv("IG_SESSION_FILE", "session.json"))
    if sess.exists():
        try:
            cl.load_settings(str(sess))
            return cl
        except Exception:
            pass  # session expire ho gaya -> neeche login try karenge

    # 2) Session na ho toh env creds se login karke session bana lo
    user = os.getenv("IG_USERNAME")
    pw = os.getenv("IG_PASSWORD")
    if user and pw:
        try:
            cl.login(user, pw)
            cl.dump_settings(str(sess))
            return cl
        except Exception:
            return None
    return None

import inspect
import time as _time


def _cursor_param_name(fn) -> str | None:
    """Cursor/pagination param ka NAAM runtime pe poochho — guess nahi."""
    try:
        params = list(inspect.signature(fn).parameters.keys())
    except Exception:
        return None
    for cand in ("pagination", "cursor", "end_cursor", "next_max_id", "max_id"):
        if cand in params:
            return cand
    return None


def fetch_instagrapi_auth_comments(
    shortcode: str,
    amount: int = 300,
    url: str | None = None,
    progress_cb=None,
) -> tuple[list[dict] | None, str]:
    """
    REAL comments, instagrapi 3.0.21 confirmed names ke saath.
    Pagination: media_comments_chunk -> (comments, cursor) loop.
    Returns (comments, error_msg). error_msg == "" means success.
    """
    cl = _get_auth_client()
    if not cl:
        return None, "No session/creds: session.json missing or login failed"

    def say(msg):
        if progress_cb:
            try:
                progress_cb(msg)
            except Exception:
                pass

    # ---- resolve media id ----
    media_id = None
    errs = []
    for nm, fn in [
        ("media_pk_from_code", lambda: cl.media_pk_from_code(shortcode)),
        ("media_id", lambda: cl.media_id(shortcode)),
    ]:
        try:
            media_id = fn()
            if media_id:
                break
        except Exception as e:
            errs.append(f"{nm}: {type(e).__name__}")
    if url and not media_id:
        try:
            media_id = cl.media_pk_from_url(url)
        except Exception as e:
            errs.append(f"media_pk_from_url: {type(e).__name__}")
    if not media_id:
        return None, "media id resolve fail: " + ", ".join(errs)

    target = max(50, min(int(amount), 1000))   # safety cap (rate-limit)
    page = min(300, target)
    collected: dict = {}
    errors: list[str] = []

    chunk_fn = getattr(cl, "media_comments_chunk", None)
    cursor_name = _cursor_param_name(chunk_fn) if callable(chunk_fn) else None

    if callable(chunk_fn):
        cursor = None
        for page_no in range(1, 9):            # hard cap 8 pages (~2400) safety
            say(f"Fetching page {page_no} (collected {len(collected)})...")
            try:
                if cursor and cursor_name:
                    res = chunk_fn(media_id, page, **{cursor_name: cursor})
                elif cursor:
                    res = chunk_fn(media_id, page, cursor)
                else:
                    res = chunk_fn(media_id, page)
            except TypeError:
                try:
                    res = chunk_fn(media_id, page)
                except Exception as e:
                    errors.append(f"chunk p{page_no}: {type(e).__name__}: {e}")
                    break
            except Exception as e:
                errors.append(f"chunk p{page_no}: {type(e).__name__}: {e}")
                break

            comments_part = res[0] if isinstance(res, (tuple, list)) and len(res) else []
            next_cursor = None
            if isinstance(res, tuple) and len(res) >= 2:
                nc = res[1]
                next_cursor = nc if isinstance(nc, str) and nc else None

            new = 0
            for c in comments_part or []:
                pk = getattr(c, "pk", None) or getattr(c, "id", None)
                text = (getattr(c, "text", "") or "").strip()
                key = pk or text
                if not text or key in collected:
                    continue
                collected[key] = c
                new += 1

            if len(collected) >= target:
                break
            if not next_cursor or new == 0:
                break
            cursor = next_cursor
            _time.sleep(1.5)                   # rate-limit safety between pages
        raw = list(collected.values())
    else:
        # fallback: single-shot
        try:
            say("Fetching comments (single call)...")
            raw = cl.media_comments(media_id, amount=target) or []
        except Exception as e:
            return None, f"media_comments fail: {type(e).__name__}: {e}"

    if not raw:
        return None, f"No comments collected. errors={errors[-3:]}"

    out: list[dict] = []
    seen: set[str] = set()
    for c in raw[:target]:
        text = (getattr(c, "text", "") or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        u = getattr(c, "user", None)
        user = (getattr(u, "username", None) or getattr(u, "user_name", None)
                or getattr(c, "user_name", None) or getattr(c, "username", None))
        out.append(normalize_comment({
            "text": text,
            "username": user,
            "likes": getattr(c, "like_count", 0),
            "timestamp": getattr(c, "created_at", None),
            "source": "instagrapi_auth",
            "post_shortcode": shortcode,
        }))

    if not out:
        return None, f"Got {len(raw)} raw but 0 usable text comments"
    return out, ""