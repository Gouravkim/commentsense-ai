from __future__ import annotations

import logging
import os

import pandas as pd

from src.aspects import aspect_flags, extract_aspects, summarize_aspects
from src.utils import prepare_text

import hashlib, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path as _Path

logger = logging.getLogger(__name__)

SENTIMENT_MAP = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive",
    "negative": "negative",
    "neutral": "neutral",
    "positive": "positive",
}

TOXIC_LABELS = {
    "toxic",
    "severe_toxic",
    "obscene",
    "threat",
    "insult",
    "identity_hate",
}

EMPTY_COLUMNS = [
    "comment_id",
    "text",
    "username_hash",
    "timestamp",
    "likes",
    "source",
    "post_shortcode",
    "sentiment",
    "sentiment_score",
    "emotion",
    "emotion_score",
    "toxicity_label",
    "toxicity_score",
    "is_toxic",
    "aspects",
    "aspect_summary",
    "flags",
]

_MODEL_CACHE: dict = {}

TOXIC_WORDS = {
    "idiot", "stupid", "shut up", "garbage", "trash", "scam", "fake",
    "hate", "worst", "pathetic", "disgusting", "insulting", "useless",
    "nonsense", "rubbish", "crap"
}

EMOTION_WORDS = {
    "joy": {"love", "amazing", "awesome", "happy", "best", "excellent", "superb", "fantastic", "great", "enjoy", "mast", "badhiya"},
    "anger": {"angry", "mad", "rage", "worst", "hate", "useless", "scam", "idiot", "shut up", "garbage", "trash"},
    "sadness": {"sad", "disappointed", "regret", "miss", "painful", "cry", "heartbreak", "kharab"},
    "surprise": {"wow", "surprised", "unexpected", "amazing", "shocking", "unbelievable"},
    "fear": {"afraid", "scared", "worried", "unsafe", "danger"},
    "disgust": {"disgusting", "gross", "cringe", "awful", "terrible", "rubbish"},
}


def _load_models(use_transformers: bool = True):
    if not use_transformers:
        return None

    if True in _MODEL_CACHE:
        return _MODEL_CACHE[True]

    if os.getenv("COMMENTSENSE_DISABLE_TRANSFORMERS", "false").lower() in {"1", "true", "yes", "y"}:
        _MODEL_CACHE[True] = None
        return None

    try:
        from transformers import pipeline

        sentiment_pipe = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment",
            truncation=True,
        )

        toxicity_pipe = pipeline(
            "text-classification",
            model="unitary/toxic-bert",
            truncation=True,
        )

        emotion_pipe = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            truncation=True,
        )

        _MODEL_CACHE[True] = (sentiment_pipe, toxicity_pipe, emotion_pipe)
    except Exception as exc:
        logger.warning("Transformer models unavailable, using rule-based fallback: %s", exc)
        _MODEL_CACHE[True] = None

    return _MODEL_CACHE[True]


def _safe_batch(pipe, texts: list[str], **kwargs):
    try:
        return pipe(texts, **kwargs)
    except Exception:
        results = []
        for text in texts:
            try:
                results.append(pipe(text, **kwargs))
            except Exception:
                try:
                    results.append(pipe(text))
                except Exception:
                    results.append([{"label": "unknown", "score": 0.0}])
        return results


def _single_result(results, index: int) -> dict:
    try:
        item = results[index]
    except Exception:
        return {"label": "unknown", "score": 0.0}

    if isinstance(item, list):
        item = item[0] if item else {}

    if isinstance(item, dict):
        return item

    return {"label": "unknown", "score": 0.0}


def _label_scores(results, index: int) -> dict[str, float]:
    try:
        item = results[index]
    except Exception:
        return {}

    if isinstance(item, dict):
        items = [item]
    elif isinstance(item, list):
        if item and isinstance(item[0], dict):
            items = item
        elif item and isinstance(item[0], list):
            items = item[0]
        else:
            items = []
    else:
        items = []

    scores = {}
    for entry in items:
        if isinstance(entry, dict):
            label = str(entry.get("label", "unknown"))
            score = float(entry.get("score", 0.0) or 0.0)
            scores[label] = score

    return scores


def _normalize_sentiment_label(label: str) -> str:
    label = str(label).strip()
    if label in SENTIMENT_MAP:
        return SENTIMENT_MAP[label]

    lowered = label.lower()
    if "pos" in lowered:
        return "positive"
    if "neg" in lowered:
        return "negative"
    return "neutral"


def _rule_sentiment(text: str) -> tuple[str, float]:
    from src.aspects import NEG_WORDS, POS_WORDS

    lower = text.lower()
    pos = sum(1 for w in POS_WORDS if w in lower)
    neg = sum(1 for w in NEG_WORDS if w in lower)

    if pos > neg:
        return "positive", min(1.0, 0.55 + (pos - neg) * 0.08)
    if neg > pos:
        return "negative", min(1.0, 0.55 + (neg - pos) * 0.08)
    return "neutral", 0.50


def _rule_toxicity(text: str) -> tuple[str, float, bool]:
    lower = text.lower()
    hits = [w for w in TOXIC_WORDS if w in lower]

    if hits:
        score = min(1.0, 0.60 + len(hits) * 0.10)
        return "toxic", score, True

    return "non_toxic", 0.05, False


def _rule_emotion(text: str) -> tuple[str, float]:
    lower = text.lower()
    scores = {}

    for emotion, words in EMOTION_WORDS.items():
        scores[emotion] = sum(1 for w in words if w in lower)

    if not scores or max(scores.values()) == 0:
        return "neutral", 0.50

    top = max(scores, key=scores.get)
    return top, min(1.0, 0.55 + scores[top] * 0.10)


ANALYSIS_CACHE_DIR = _Path(".cache/analysis")


def _cache_key(texts: list[str], use_transformers: bool) -> str:
    h = hashlib.md5()
    h.update(("t" if use_transformers else "r").encode())
    for t in texts:
        h.update(t.encode("utf-8", "ignore"))
    return h.hexdigest()


def analyze_comments(records, use_transformers: bool = True, progress_cb=None) -> pd.DataFrame:
    print(f"[analyzer] START: {len(records)} records, use_transformers={use_transformers}")  # <-- ADD THIS
    
    if not records:
        return pd.DataFrame(columns=EMPTY_COLUMNS)
    
    print("[analyzer] Preparing texts...")  # <-- ADD THIS
    prepared = []
    """
    Batch + PARALLEL models + chunked progress + disk cache.
    progress_cb(fraction 0-1, message) optional.
    """
    if not records:
        return pd.DataFrame(columns=EMPTY_COLUMNS)

    prepared = []
    for rec in records:
        if isinstance(rec, str):
            rec = {"text": rec}
        text = prepare_text(rec.get("text", ""))
        if not text:
            continue
        prepared.append(({
            "comment_id": rec.get("comment_id"),
            "text": text,
            "username_hash": rec.get("username_hash"),
            "timestamp": rec.get("timestamp"),
            "likes": rec.get("likes", 0),
            "source": rec.get("source", "unknown"),
            "post_shortcode": rec.get("post_shortcode"),
        }, text))

    if not prepared:
        return pd.DataFrame(columns=EMPTY_COLUMNS)

    texts = [t for _, t in prepared]

    # ---- CACHE HIT? ----
    key = _cache_key(texts, use_transformers)
    cfile = ANALYSIS_CACHE_DIR / f"{key}.csv"
    if cfile.exists():
        try:
            df = pd.read_csv(cfile)
            df["aspects"] = df["aspects"].apply(lambda s: json.loads(s) if isinstance(s, str) else s)
            df["flags"] = df["flags"].apply(lambda s: json.loads(s) if isinstance(s, str) else s)
            if progress_cb:
                progress_cb(1.0, "Analysis cache hit — instant result.")
            print(f"[analyzer] CACHE HIT ({len(df)} comments) -> instant")
            return df
        except Exception:
            pass

        print("[analyzer] Loading models...")  # <-- ADD THIS
    models = _load_models(use_transformers=use_transformers)
    print(f"[analyzer] Models loaded: {models is not None}")  # <-- ADD THISmodels = _load_models(use_transformers=use_transformers)
    rows: list[dict] = []
    total = len(texts)
    done = 0
    t0 = time.time()

    for start in range(0, total, 25):
        chunk_texts = texts[start:start + 25]
        chunk_prepared = prepared[start:start + 25]

        if models:
            sentiment_pipe, toxicity_pipe, emotion_pipe = models
            # 3 models PARALLEL -> wall time = max, not sum (~3x faster)
            with ThreadPoolExecutor(max_workers=3) as ex:
                f_s = ex.submit(_safe_batch, sentiment_pipe, chunk_texts, batch_size=32)
                f_e = ex.submit(_safe_batch, emotion_pipe, chunk_texts, batch_size=32)
                f_t = ex.submit(_safe_batch, toxicity_pipe, chunk_texts, top_k=None, batch_size=32)
                sent_results = f_s.result()
                emo_results = f_e.result()
                tox_results = f_t.result()
        else:
            sent_results = emo_results = tox_results = None

        for idx, (base, text) in enumerate(chunk_prepared):
            if models:
                sent = _single_result(sent_results, idx)
                emo = _single_result(emo_results, idx)
                tox_scores = _label_scores(tox_results, idx)

                sentiment = _normalize_sentiment_label(sent.get("label", "neutral"))
                sentiment_score = float(sent.get("score", 0.0) or 0.0)
                emotion = str(emo.get("label", "neutral")).lower()
                emotion_score = float(emo.get("score", 0.0) or 0.0)

                toxic_hits = {l: s for l, s in tox_scores.items() if l in TOXIC_LABELS and s > 0.5}
                is_toxic = bool(toxic_hits)
                if is_toxic:
                    toxicity_label = max(toxic_hits, key=toxic_hits.get)
                    toxicity_score = toxic_hits[toxicity_label]
                else:
                    toxicity_label = "non_toxic"
                    toxicity_score = max(tox_scores.values()) if tox_scores else 0.0
            else:
                sentiment, sentiment_score = _rule_sentiment(text)
                emotion, emotion_score = _rule_emotion(text)
                toxicity_label, toxicity_score, is_toxic = _rule_toxicity(text)

            aspects = extract_aspects(text, sentiment, sentiment_score)
            flags = aspect_flags(aspects)
            if is_toxic:
                flags.append("toxic_comment")

            rows.append({
                **base,
                "sentiment": sentiment,
                "sentiment_score": round(sentiment_score, 4),
                "emotion": emotion,
                "emotion_score": round(emotion_score, 4),
                "toxicity_label": toxicity_label,
                "toxicity_score": round(toxicity_score, 4),
                "is_toxic": bool(is_toxic),
                "aspects": aspects,
                "aspect_summary": summarize_aspects(aspects),
                "flags": flags,
            })

        done += len(chunk_texts)
        dt = time.time() - t0
        ms_per = (dt / max(done, 1)) * 1000
        print(f"[analyzer] {done}/{total} comments in {dt:.1f}s ({ms_per:.0f} ms/comment)")
        if progress_cb:
            progress_cb(done / total, f"Analyzing {done}/{total} comments...")

    df = pd.DataFrame(rows, columns=EMPTY_COLUMNS)

    # ---- CACHE SAVE (aspects/flags JSON-stringify karke) ----
    try:
        ANALYSIS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        save_df = df.copy()
        save_df["aspects"] = save_df["aspects"].apply(lambda d: json.dumps(d, default=str))
        save_df["flags"] = save_df["flags"].apply(lambda f: json.dumps(f, default=str))
        save_df.to_csv(cfile, index=False)
        print(f"[analyzer] cache saved -> {cfile}")
    except Exception:
        pass

    return df