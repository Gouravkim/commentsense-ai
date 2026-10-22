from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pandas as pd

POLL_FILE = Path("data/poll_votes.json")


def detect_duplicate_ballots(texts) -> dict:
    # Ballot stuffing detection: same text multiple baar
    counts = pd.Series(list(texts), dtype="object").value_counts()
    dups = counts[counts > 1]
    return {str(t): int(c) for t, c in dups.items()}


def compute_social_ballot(df: pd.DataFrame, dedupe: bool = True) -> dict:
    # Har comment = ek ballot. Toxic = invalid. Duplicate = bot vote.
    if df is None or df.empty:
        return {"total": 0, "for": 0, "against": 0, "abstain": 0, "invalid": 0,
                "duplicates": {}, "dup_extra": 0, "decided": 0, "turnout": 0.0,
                "margin": 0.0, "leader": "NONE", "integrity": 0.0,
                "verdict": "NO DATA"}

    total = len(df)
    invalid = int(df["is_toxic"].sum()) if "is_toxic" in df.columns else 0
    pool = df[df["is_toxic"] != True] if "is_toxic" in df.columns else df.copy()

    dups = detect_duplicate_ballots(pool["text"].tolist())
    dup_extra = int(sum(c - 1 for c in dups.values()))

    if dedupe:
        pool = pool.drop_duplicates(subset=["text"])

    for_v = int((pool["sentiment"] == "positive").sum())
    against = int((pool["sentiment"] == "negative").sum())
    abstain = int((pool["sentiment"] == "neutral").sum())

    decided = for_v + against
    turnout = (decided / total * 100) if total else 0.0

    if decided:
        for_pct = for_v / decided * 100
        against_pct = against / decided * 100
        margin = abs(for_pct - against_pct)
        leader = "FOR" if for_v > against else ("AGAINST" if against > for_v else "TIE")
    else:
        margin = 0.0
        leader = "TIE"

    toxic_pct = (invalid / total * 100) if total else 0.0
    dup_pct = (dup_extra / total * 100) if total else 0.0
    integrity = max(0.0, min(100.0, 100 - toxic_pct - dup_pct))

    if decided == 0:
        verdict = "NO VALID VOTES"
    elif leader == "TIE":
        verdict = "TIE - NO CLEAR MANDATE"
    else:
        verdict = leader + " WINS"

    return {"total": total, "for": for_v, "against": against, "abstain": abstain,
            "invalid": invalid, "duplicates": dups, "dup_extra": dup_extra,
            "decided": decided, "turnout": turnout, "margin": margin,
            "leader": leader, "integrity": integrity, "verdict": verdict}


def load_poll_votes() -> dict:
    if POLL_FILE.exists():
        try:
            data = json.loads(POLL_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "votes" in data:
                return data
        except Exception:
            pass
    return {"votes": {}}


def cast_vote(voter_id: str, choice: str):
    # Double-vote protection: voter ID ka hash store hota hai
    voter_id = (voter_id or "").strip().lower()
    if not voter_id:
        return False, "Voter ID empty hai."
    data = load_poll_votes()
    key = hashlib.sha256(voter_id.encode("utf-8")).hexdigest()[:16]
    if key in data["votes"]:
        return False, "Duplicate vote BLOCKED - is Voter ID se pehle hi vote ho chuka hai."
    data["votes"][key] = {"choice": choice, "ts": time.time()}
    POLL_FILE.parent.mkdir(parents=True, exist_ok=True)
    POLL_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return True, "Vote recorded: " + choice + " (voter hash: " + key + ")"
