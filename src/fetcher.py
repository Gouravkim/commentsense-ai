from __future__ import annotations
import time
import os
from src.cache import get_cached_comments, set_cached_comments
from src.providers import (
    fetch_instagrapi_comments,
    fetch_instagrapi_auth_comments,
    fetch_official_api_comments,
    load_csv_dataframe,
    load_demo,
)
from src.utils import extract_shortcode


def get_comments_from_url(
    url: str,
    amount: int = 100,
    allow_fallback: bool = True,
    demo_dataset: str = "demo_mixed.csv",
    progress_cb=None,
) -> tuple[list[dict], str]:
    """
    Returns (comments, source) with TIMING LOGS for each tier.
    """
    def say(msg):
        print(f"[fetcher] {msg}")
        if progress_cb:
            try:
                progress_cb(msg)
            except Exception:
                pass

    t_start = time.time()
    shortcode = extract_shortcode(url)
    if not shortcode:
        return [], "invalid_url"

    # Cache check
    cached = get_cached_comments(shortcode)
    if cached:
        say(f"CACHE HIT ({len(cached)} comments, {time.time()-t_start:.2f}s)")
        return cached, "cache"

    comments = None
    source = "unknown"
    auth_error = ""

    # Tier 1: official / authorized local JSON (optional)
    t0 = time.time()
    say("Tier-1: official API check...")
    comments = fetch_official_api_comments(shortcode, amount=amount)
    dt1 = time.time() - t0
    say(f"Tier-1 done in {dt1:.2f}s -> {'HIT' if comments else 'miss'}")
    if comments:
        source = "official_api"

    # Tier 2: anonymous — AB DEFAULT OFF (75s waste, hamesha fail).
    # Zaroorat ho toh: set COMMENTSENSE_TRY_ANONYMOUS=true
    if not comments and os.getenv("COMMENTSENSE_TRY_ANONYMOUS", "false").lower() in {"1", "true", "yes"}:
        t0 = time.time()
        say("Tier-2: anonymous instagrapi...")
        comments = fetch_instagrapi_comments(shortcode, amount=amount)
        dt2 = time.time() - t0
        say(f"Tier-2 done in {dt2:.2f}s -> {'HIT' if comments else 'miss'}")
        if comments:
            source = "instagrapi"

    # Tier 2.5: AUTHENTICATED burner -> REAL comments  ⭐
    if not comments:
        t0 = time.time()
        say("Tier-2.5: authenticated burner...")
        comments, auth_error = fetch_instagrapi_auth_comments(
            shortcode, amount=amount, url=url, progress_cb=progress_cb
        )
        dt25 = time.time() - t0
        say(f"Tier-2.5 done in {dt25:.2f}s -> {'HIT' if comments else 'miss'} | err={auth_error[:300]}")
        if comments:
            source = "instagrapi_auth"

    if comments:
        set_cached_comments(shortcode, comments)
        say(f"TOTAL FETCH: {time.time()-t_start:.2f}s -> source={source}, {len(comments)} comments")
        return comments, source

    # Tier 3: graceful fallback (demo safety net)
    if allow_fallback:
        say(f"ALL TIERS FAILED ({time.time()-t_start:.2f}s). Falling back to demo.")
        return load_demo(demo_dataset), f"fallback_demo|{auth_error}"

    return [], f"failed|{auth_error}"


def get_comments_from_csv_file(uploaded_file) -> list[dict]:
    import pandas as pd
    df = pd.read_csv(uploaded_file)
    return load_csv_dataframe(df)