# add_voting.py -> app.py ko "AI-Based Social Voting System" mein pivot karta hai
# aur src/voting.py + naya Voting tab add karta hai.
from pathlib import Path

# ---------- 1) src/voting.py banao ----------
VOTING_PY = '''from __future__ import annotations

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
'''

Path("src").mkdir(exist_ok=True)
Path("src/voting.py").write_text(VOTING_PY, encoding="utf-8")
print("src/voting.py created")

# ---------- 2) app.py patch karo ----------
p = Path("app.py")
s = p.read_text(encoding="utf-8")
log = []

# 2a) imports
if "from src.voting import" not in s:
    anchor = "from src.summary import generate_executive_summary"
    if anchor in s:
        s = s.replace(anchor, anchor + "\nfrom src.voting import compute_social_ballot, cast_vote, load_poll_votes", 1)
        log.append("voting imports added")
if "import json" not in s.split("\n\n")[0] + s[:400]:
    s = s.replace("import re\n", "import json\nimport re\n", 1)
    log.append("json import added")

# 2b) rebrand title
if 'page_title="CommentSense AI"' in s:
    s = s.replace('page_title="CommentSense AI"', 'page_title="AI-Based Social Voting System"')
    s = s.replace('page_icon="🧠"', 'page_icon="🗳️"')
    log.append("page config rebranded")
if 'st.title("🧠 CommentSense AI")' in s:
    s = s.replace('st.title("🧠 CommentSense AI")',
                  'st.title("🗳️ AI-Based Social Voting System")\n'
                  'st.caption("Powered by CommentSense AI engine — sentiment • toxicity • emotion • aspects")')
    log.append("title rebranded")
old_cap = "st.caption(\"Instagram comments ko sentiment, toxicity, emotion, aspect insights aur brand intelligence mein convert karo.\")"
if old_cap in s:
    s = s.replace(old_cap,
                  'st.caption("Public social comments ko AI-powered FOR / AGAINST / ABSTAIN votes mein convert karke '
                  'transparent, manipulation-proof voting results nikalne wala intelligent system.")')
    log.append("caption rebranded")

# 2c) tabs line -> 4 tabs
old_tabs = 'tab_insights, tab_comments, tab_report = st.tabs(["📊 Insights", "💬 Comment Explorer", "📄 Report"])'
new_tabs = 'tab_insights, tab_vote, tab_comments, tab_report = st.tabs(["📊 Insights", "🗳️ Social Voting", "💬 Comment Explorer", "📄 Report"])'
if old_tabs in s:
    s = s.replace(old_tabs, new_tabs)
    log.append("tabs updated (Voting tab added)")

# 2d) Voting tab block insert (Comment Explorer se pehle)
VOTING_TAB = '''with tab_vote:
    st.subheader("🗳️ Social Ballot — Har Comment Ek Vote")
    poll_q = st.text_input("Poll Question / Proposal",
                           value="Should this proposal / campaign be accepted?")
    dedupe = st.checkbox("Remove duplicate / bot ballots before counting", value=True)

    ballot = compute_social_ballot(df, dedupe=dedupe)

    b1, b2, b3, b4, b5 = st.columns(5)
    b1.metric("✅ FOR Votes", ballot["for"])
    b2.metric("❌ AGAINST Votes", ballot["against"])
    b3.metric("😐 ABSTAIN", ballot["abstain"])
    b4.metric("🚫 Invalid Ballots (Toxic)", ballot["invalid"])
    b5.metric("🛡️ Vote Integrity", f"{ballot['integrity']:.0f}/100")

    t1, t2 = st.columns(2)
    t1.metric("Decided Turnout", f"{ballot['turnout']:.1f}%")
    t2.metric("Winning Margin", f"{ballot['margin']:.1f}%")

    if ballot["integrity"] < 50:
        v_class = "alert-critical"
        v_text = f"⚠️ RESULT UNRELIABLE — manipulation suspected (integrity {ballot['integrity']:.0f}/100)"
    elif ballot["verdict"].startswith("TIE"):
        v_class = "alert-monitor"
        v_text = "🤝 TIE — No clear mandate"
    elif ballot["leader"] == "FOR":
        v_class = "alert-healthy"
        v_text = f"✅ VERDICT: FOR WINS by {ballot['margin']:.1f}% margin"
    elif ballot["leader"] == "AGAINST":
        v_class = "alert-critical"
        v_text = f"❌ VERDICT: AGAINST WINS by {ballot['margin']:.1f}% margin"
    else:
        v_class = "alert-monitor"
        v_text = "No valid votes yet"

    st.markdown(
        f'<div class="{v_class}"><div style="font-size:1.4rem;">{v_text}</div>'
        f'<div style="font-weight:normal;opacity:.9;">Poll: {poll_q}</div></div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        vote_df = pd.DataFrame({
            "Vote": ["FOR", "AGAINST", "ABSTAIN"],
            "Count": [ballot["for"], ballot["against"], ballot["abstain"]],
        })
        fig_vote = px.pie(
            vote_df, names="Vote", values="Count", title="Vote Distribution",
            color="Vote",
            color_discrete_map={"FOR": "#22c55e", "AGAINST": "#ef4444", "ABSTAIN": "#94a3b8"},
        )
        st.plotly_chart(theme_fig(fig_vote), width="stretch")
    with c2:
        if ballot["duplicates"]:
            st.markdown("**🕵️ Ballot Stuffing Evidence (duplicate ballots):**")
            dup_df = pd.DataFrame(
                [{"Text": (t[:80] + "…" if len(t) > 80 else t), "Copies": c}
                 for t, c in ballot["duplicates"].items()]
            ).sort_values("Copies", ascending=False).head(10)
            st.dataframe(dup_df, width="stretch", hide_index=True)
        else:
            st.success("No duplicate ballots detected — vote pool clean.")

    st.divider()
    st.subheader("🧍 In-App Manual Voting (Double-Vote Protected)")
    with st.form("manual_vote_form"):
        mv1, mv2 = st.columns(2)
        with mv1:
            voter_id = st.text_input("Voter ID / Email")
        with mv2:
            choice = st.radio("Your Vote", ["FOR", "AGAINST", "ABSTAIN"], horizontal=True)
        submitted = st.form_submit_button("Cast Vote 🔒")
        if submitted:
            if not voter_id.strip():
                st.error("Voter ID zaroori hai.")
            else:
                ok, msg = cast_vote(voter_id, choice)
                if ok:
                    st.success(msg)
                else:
                    st.warning(msg)

    manual = load_poll_votes()
    if manual["votes"]:
        mcounts = pd.Series([v["choice"] for v in manual["votes"].values()]).value_counts()
        st.markdown(f"**Manual votes recorded:** {len(manual['votes'])} — "
                    + ", ".join(f"{k}: {v}" for k, v in mcounts.items()))
    else:
        st.caption("Abhi tak koi manual vote nahi.")

    result_payload = {
        "poll_question": poll_q,
        "social_ballot": ballot,
        "manual_votes": len(manual["votes"]),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    st.download_button(
        "⬇️ Download Voting Result (JSON)",
        data=json.dumps(result_payload, indent=2, default=str).encode("utf-8"),
        file_name="voting_result.json",
        mime="application/json",
        width="stretch",
    )

'''

if "with tab_vote:" not in s:
    j = s.find("# Comment Explorer tab")
    if j == -1:
        print("ERROR: '# Comment Explorer tab' marker nahi mila. Kuch nahi badla.")
        raise SystemExit(1)
    k = s.rfind("# ----", 0, j)
    if k == -1:
        k = j
    s = s[:k] + VOTING_TAB + "\n" + s[k:]
    log.append("Voting tab inserted")

p.write_text(s, encoding="utf-8")
print("✅ app.py pivot ho gaya:")
for line in log:
    print("   -", line)