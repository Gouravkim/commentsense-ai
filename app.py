from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analyzer import analyze_comments
from src.cache import clear_cache
from src.fetcher import get_comments_from_csv_file, get_comments_from_url
from src.metrics import calculate_brand_health, get_risk_status
from src.providers import load_demo
from src.report import export_csv, export_json, export_pdf_report
from src.summary import generate_executive_summary
from src.voting import compute_social_ballot, cast_vote, load_poll_votes

import streamlit as st
def theme_fig(fig, height=380):
    """FIX #5 & #6: dark-theme aware + uniform height charts."""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#FAFAFA", "size": 13},
        legend={"font": {"color": "#FAFAFA"}},
        margin={"t": 50, "b": 40, "l": 40, "r": 20},
    )
    return fig
st.set_page_config(
    page_title="AI-Based Social Voting System",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ✨ PREMIUM UI CSS INJECTION ✨
st.markdown("""
<style>
    .stApp { font-family: 'Inter', 'Segoe UI', sans-serif; }

    /* Glass metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 16px;
        padding: 18px 15px;
        box-shadow: 0 8px 32px 0 rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(255,255,255,0.3);
    }
    [data-testid="stMetricLabel"] { font-size: 0.85rem !important; font-weight: 600 !important; opacity: 0.85; }

    /* FIX #1 & #9: truncation hatao */
    [data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        font-weight: 800 !important;
        overflow: visible !important;
        text-overflow: clip !important;
        white-space: normal !important;
    }

    /* FIX #3: Summary dark-glass card (white-on-white khatam) */
    .summary-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 16px;
        padding: 20px 24px;
        color: #FAFAFA;
        white-space: pre-wrap;
        font-size: 0.98rem;
        line-height: 1.8;
        box-shadow: 0 8px 32px 0 rgba(0,0,0,0.2);
    }

    /* FIX #4: charon alert levels ke alag colors */
    .alert-critical { padding: 20px; border-radius: 12px; color: #fff; font-weight: 600;
        background: linear-gradient(90deg, #ff416c, #ff4b2b);
        box-shadow: 0 4px 18px rgba(255,75,43,0.4); margin-bottom: 20px; border-left: 5px solid #fff; }
    .alert-warning  { padding: 20px; border-radius: 12px; color: #fff; font-weight: 600;
        background: linear-gradient(90deg, #f7971e, #f5533d);
        box-shadow: 0 4px 18px rgba(245,83,61,0.35); margin-bottom: 20px; border-left: 5px solid #fff; }
    .alert-monitor  { padding: 20px; border-radius: 12px; color: #1f2937; font-weight: 600;
        background: linear-gradient(90deg, #ffd200, #f7971e);
        box-shadow: 0 4px 18px rgba(247,151,30,0.35); margin-bottom: 20px; border-left: 5px solid #fff; }
    .alert-healthy  { padding: 20px; border-radius: 12px; color: #fff; font-weight: 600;
        background: linear-gradient(90deg, #11998e, #38ef7d);
        box-shadow: 0 4px 18px rgba(56,239,125,0.3); margin-bottom: 20px; border-left: 5px solid #fff; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 24px; border-radius: 8px 8px 0 0; background-color: rgba(255,255,255,0.05); }
</style>
""", unsafe_allow_html=True)

# ... (baaki ka tera purana code jaisa hai waisa hi rehne de) ...

# -----------------------------
# Sidebar settings
# -----------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    amount = st.slider("Comments to fetch", min_value=20, max_value=300, value=100, step=20)
    max_analyze = st.slider("Max comments to analyze (speed vs coverage)",
                            min_value=50, max_value=500, value=150, step=50,
                            help="Fetch jitna chaaho utna karo, par analysis isi limit tak — demo fast rahega.")
    allow_fallback = st.checkbox("Auto fallback to demo data", value=True)
    demo_dataset = st.selectbox(
        "Demo dataset",
        options=[
            "demo_mixed.csv",
            "demo_healthy.csv",
            "demo_crisis.csv",
            "demo_hinglish.csv",
        ],
    )
    fast_mode = st.checkbox(
        "Fast rule-based mode",
        value=False,
        help="Use this if Hugging Face model download is slow or unavailable.",
    )

    if st.button("Clear cache"):
        clear_cache()
        st.success("Cache cleared.")

# -----------------------------
# Session defaults
# -----------------------------
if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame()

if "source" not in st.session_state:
    st.session_state["source"] = None

if "metadata" not in st.session_state:
    st.session_state["metadata"] = {}

if "analyzed_at" not in st.session_state:
    st.session_state["analyzed_at"] = None

if "last_csv_id" not in st.session_state:
    st.session_state["last_csv_id"] = None


def store_and_analyze(comments: list, source: str, metadata: dict | None = None) -> None:
    if not comments:
        st.error("No comments found. Try demo data or another URL.")
        return

    sample = comments[:max_analyze] if len(comments) > max_analyze else comments
    progress_text = st.empty()
    progress_text.text(f"Analyzing 0/{len(sample)} comments...")
    
    def _cb(frac, msg=""):
        try:
            progress_text.text(msg or f"Analyzing {int(frac*100)}%...")
        except Exception:
            pass
    
    df = analyze_comments(sample, use_transformers=not fast_mode, progress_cb=_cb)
    progress_text.empty()

    st.session_state["df"] = df
    st.session_state["source"] = source
    st.session_state["metadata"] = metadata or {}
    st.session_state["analyzed_at"] = datetime.now(timezone.utc).isoformat()


# -----------------------------
# Header
# -----------------------------
st.title("🗳️ AI-Based Social Voting System")
st.caption("Powered by CommentSense AI engine — sentiment • toxicity • emotion • aspects")
st.caption("Public social comments ko AI-powered FOR / AGAINST / ABSTAIN votes mein convert karke transparent, manipulation-proof voting results nikalne wala intelligent system.")

# -----------------------------
# Inputs
# -----------------------------
col_url, col_btn = st.columns([4, 1])

with col_url:
    url = st.text_input(
        "Instagram Post / Reel URL",
        placeholder="https://www.instagram.com/p/CjPUjEvDKT4/",
    )

with col_btn:
    st.write("")
    st.write("")
    analyze_url_btn = st.button("Analyze URL", type="primary", width="stretch")

col_csv, col_demo, col_reset = st.columns([3, 1, 1])

with col_csv:
    csv_file = st.file_uploader("Upload CSV", type=["csv"])

with col_demo:
    st.write("")
    st.write("")
    demo_btn = st.button("Run Demo", width="stretch")

with col_reset:
    st.write("")
    st.write("")
    reset_btn = st.button("Reset", width="stretch")

# -----------------------------
# Actions
# -----------------------------
if analyze_url_btn:
    if not url:
        st.error("Please enter an Instagram URL.")
    else:
        fetch_status = st.status("Fetching comments...", expanded=True)
        def _fetch_cb(msg):
            try:
                fetch_status.update(label=msg)
            except Exception:
                pass
        with fetch_status:
            comments, source = get_comments_from_url(
                url=url,
                amount=amount,
                allow_fallback=allow_fallback,
                demo_dataset=demo_dataset,
                progress_cb=_fetch_cb,
            )
        fetch_status.update(label=f"Fetch done ({len(comments)} comments, source={source.split('|')[0]})", state="complete")

        metadata = {
            "url": url,
            "requested_amount": amount,
        }

        if source == "invalid_url":
            st.error("Invalid Instagram URL. Use /p/, /reel/, or /tv/ link.")
        elif source == "cache":
            st.info("Using cached comments for this post.")
        elif source in {"instagrapi", "official_api"}:
            st.success(f"Live comments fetched using {source}.")
        elif source == "fallback_demo":
            st.warning("Live fetch failed/unavailable. Using authorized demo dataset.")
        elif source == "failed":
            st.error(
                "Live fetch fail hua aur fallback OFF tha. "
                "Sidebar mein 'Auto fallback to demo data' tick karo, "
                "ya neeche button se turant demo load karo."
            )
            if st.button("⚡ Load Demo Data Now", key="force_demo_after_fail"):
                comments = load_demo(demo_dataset)
                source = "demo"
                metadata["dataset"] = demo_dataset

        if comments:
            store_and_analyze(comments, source, metadata)

if demo_btn:
    comments = load_demo(demo_dataset)
    store_and_analyze(comments, "demo", {"dataset": demo_dataset})

if csv_file is not None:
    file_id = (csv_file.name, getattr(csv_file, "size", None))
    if st.session_state.get("last_csv_id") != file_id:
        st.session_state["last_csv_id"] = file_id
        try:
            comments = get_comments_from_csv_file(csv_file)
            store_and_analyze(comments, "csv", {"filename": csv_file.name})
        except Exception as exc:
            st.error(f"CSV upload failed: {exc}")

if reset_btn:
    for key in ["df", "source", "metadata", "analyzed_at", "last_csv_id"]:
        st.session_state.pop(key, None)
    st.rerun()

# -----------------------------
# Display results
# -----------------------------
df = st.session_state.get("df", pd.DataFrame())

if df.empty:
    st.info("👈 Paste an Instagram URL, upload a CSV, or click **Run Demo** to start.")
    st.stop()

metadata = {
    **st.session_state.get("metadata", {}),
    "source": st.session_state.get("source"),
    "analyzed_at": st.session_state.get("analyzed_at"),
}

health = calculate_brand_health(df)
risk = get_risk_status(df)
summary = generate_executive_summary(df, metadata)

positive_pct = float((df["sentiment"] == "positive").mean() * 100) if "sentiment" in df else 0.0
negative_pct = float((df["sentiment"] == "negative").mean() * 100) if "sentiment" in df else 0.0
neutral_pct = float((df["sentiment"] == "neutral").mean() * 100) if "sentiment" in df else 0.0
toxic_pct = float(df["is_toxic"].mean() * 100) if "is_toxic" in df else 0.0

if "emotion" in df and not df["emotion"].empty:
    top_emotion = df["emotion"].value_counts().index[0]
else:
    top_emotion = "neutral"

# Metric cards
m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
m1.metric("Total Comments", f"{len(df)}")
m2.metric("Brand Health (/100)", f"{health:.0f}")
m3.metric("Positive", f"{positive_pct:.1f}%")
m4.metric("Neutral", f"{neutral_pct:.1f}%")
m5.metric("Negative", f"{negative_pct:.1f}%")
m6.metric("Toxic", f"{toxic_pct:.1f}%")
m7.metric("Top Emotion", str(top_emotion).title())

if len(df) < 30:
    st.warning(
        f"⚠️ Low sample size: sirf {len(df)} comments mile. "
        "Insights ki statistical confidence kam hogi — fetch amount badhao ya koi active post try karo."
    )
st.markdown(f"### Risk Status: {risk['emoji']} {risk['label']}")
st.caption(risk["reason"])

SOURCE_LABELS = {
    "instagrapi_auth": "📡 Live Instagram (authenticated / REAL comments)",
    "demo": "🎬 Demo dataset",
    "csv": "📄 Uploaded CSV",
    "cache": "🗃️ Cached live comments",
    "instagrapi": "📡 Live Instagram (instagrapi)",
    "official_api": "📡 Live Instagram (official API)",
    "fallback_demo": "🎬 Fallback demo dataset (live fetch unavailable)",
}
_current_source = st.session_state.get("source")
st.caption(
    f"**Data source:** {SOURCE_LABELS.get(_current_source, _current_source or 'unknown')} "
    f"· analyzed at {st.session_state.get('analyzed_at', '—')}"
)

# Tabs
tab_insights, tab_vote, tab_comments, tab_report = st.tabs(["📊 Insights", "🗳️ Social Voting", "💬 Comment Explorer", "📄 Report"])

# -----------------------------
# Insights tab
# -----------------------------
with tab_insights:

    # Dark-theme + uniform height helper
    def theme_fig(fig, height=380):
        fig.update_layout(
            height=height,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#FAFAFA", "size": 13},
            legend={"font": {"color": "#FAFAFA"}},
            margin={"t": 50, "b": 40, "l": 40, "r": 20},
        )
        return fig

    col1, col2 = st.columns(2)

    with col1:
        sentiment_order = ["positive", "neutral", "negative"]
        sentiment_counts = (
            df["sentiment"].value_counts()
            .reindex(sentiment_order)
            .fillna(0)
            .astype(int)
            .reset_index()
        )
        sentiment_counts.columns = ["Sentiment", "Count"]
        sentiment_counts["Sentiment"] = sentiment_counts["Sentiment"].str.title()

        fig1 = px.pie(
            sentiment_counts,
            names="Sentiment",
            values="Count",
            title="Sentiment Distribution",
            color="Sentiment",
            color_discrete_map={
                "Positive": "#22c55e",
                "Neutral": "#94a3b8",
                "Negative": "#ef4444",
            },
        )
        st.plotly_chart(theme_fig(fig1), width="stretch")

    with col2:
        emotion_order = ["joy", "neutral", "anger", "sadness", "surprise", "fear", "disgust"]
        emotion_counts = (
            df["emotion"].value_counts()
            .reindex(emotion_order)
            .fillna(0)
            .astype(int)
            .reset_index()
        )
        emotion_counts.columns = ["Emotion", "Count"]
        emotion_counts["Emotion"] = emotion_counts["Emotion"].str.title()

        fig2 = px.bar(
            emotion_counts,
            x="Emotion",
            y="Count",
            title="Emotion Breakdown",
            color="Emotion",
            color_discrete_map={
                "Joy": "#facc15",
                "Neutral": "#94a3b8",
                "Anger": "#ef4444",
                "Sadness": "#3b82f6",
                "Surprise": "#a78bfa",
                "Fear": "#14b8a6",
                "Disgust": "#f97316",
            },
        )
        st.plotly_chart(theme_fig(fig2), width="stretch")

    col3, col4 = st.columns(2)

    with col3:
        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=toxic_pct,
                number={"font": {"size": 42, "color": "#FAFAFA"}},
                title={"text": "Toxic Risk %", "font": {"size": 16, "color": "#FAFAFA"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#FAFAFA", "tickfont": {"color": "#FAFAFA"}},
                    "bar": {"color": "#ef4444", "thickness": 0.35},
                    "bgcolor": "rgba(255,255,255,0.06)",
                    "borderwidth": 1,
                    "bordercolor": "rgba(255,255,255,0.2)",
                    "steps": [
                        {"range": [0, 5], "color": "rgba(34,197,94,0.25)"},
                        {"range": [5, 10], "color": "rgba(250,204,21,0.25)"},
                        {"range": [10, 20], "color": "rgba(249,115,22,0.30)"},
                        {"range": [20, 100], "color": "rgba(239,68,68,0.35)"},
                    ],
                    "threshold": {
                        "line": {"color": "#FAFAFA", "width": 3},
                        "thickness": 0.8,
                        "value": 20,
                    },
                },
            )
        )
        st.plotly_chart(theme_fig(fig_gauge), width="stretch")

    with col4:
        aspect_rows = []
        aspects_list = df["aspects"].tolist() if "aspects" in df.columns else []

        for aspects in aspects_list:
            if not isinstance(aspects, dict):
                continue
            for aspect, info in aspects.items():
                sentiment = "neutral"
                if isinstance(info, dict):
                    sentiment = info.get("sentiment", "neutral")
                aspect_rows.append({
                    "Aspect": str(aspect).title(),
                    "Sentiment": sentiment,
                })

        if aspect_rows:
            aspect_df = pd.DataFrame(aspect_rows)
            aspect_counts = (
                aspect_df
                .groupby(["Aspect", "Sentiment"])
                .size()
                .reset_index(name="Count")
            )
            aspect_counts["Sentiment"] = aspect_counts["Sentiment"].str.title()

            fig_aspect = px.bar(
                aspect_counts,
                x="Aspect",
                y="Count",
                color="Sentiment",
                barmode="stack",
                title="Aspect-Based Sentiment",
                color_discrete_map={
                    "Positive": "#22c55e",
                    "Neutral": "#94a3b8",
                    "Negative": "#ef4444",
                },
            )
            st.plotly_chart(theme_fig(fig_aspect), width="stretch")
        else:
            st.info("No aspect keywords detected in this sample.")

    st.subheader("🧾 Executive Summary")
    from xml.sax.saxutils import escape
    st.markdown(
        f'<div class="summary-card">{escape(summary)}</div>',
        unsafe_allow_html=True,
    )

    st.subheader("🚨 Crisis & Action Alert")
    alert_class = {
        "critical": "alert-critical",
        "warning": "alert-warning",
        "monitor": "alert-monitor",
    }.get(risk["level"], "alert-healthy")

    st.markdown(
        f"""
        <div class="{alert_class}">
            <div style="font-size: 1.5rem; margin-bottom: 8px;">{risk['emoji']} {risk['label']}</div>
            <div style="font-weight: normal; opacity: 0.9;">{risk['action']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with tab_vote:
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


# -----------------------------
# Comment Explorer tab
# -----------------------------
with tab_comments:
    st.subheader("Filters")

    aspects_for_filters = df["aspects"].tolist() if "aspects" in df.columns else []

    all_aspects_set = set()
    for aspects in aspects_for_filters:
        if isinstance(aspects, dict):
            all_aspects_set.update(aspects.keys())

    all_aspects = sorted(all_aspects_set)

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        sentiment_filter = st.multiselect(
            "Sentiment",
            options=["positive", "neutral", "negative"],
        )

    with f2:
        emotion_options = sorted(df["emotion"].dropna().unique().tolist()) if "emotion" in df else []
        emotion_filter = st.multiselect("Emotion", options=emotion_options)

    with f3:
        aspect_filter = st.multiselect("Aspect", options=all_aspects)

    with f4:
        search_query = st.text_input("Search text")

    toxic_only = st.checkbox("Show toxic comments only", value=False)
    reveal_toxic = st.checkbox("Reveal toxic comment text", value=False)

    filtered = df.copy()

    if sentiment_filter:
        filtered = filtered[filtered["sentiment"].isin(sentiment_filter)]

    if emotion_filter:
        filtered = filtered[filtered["emotion"].isin(emotion_filter)]

    if toxic_only:
        filtered = filtered[filtered["is_toxic"] == True]

    if search_query:
        filtered = filtered[filtered["text"].str.contains(search_query, case=False, na=False)]

    if aspect_filter:
        def has_selected_aspect(aspects):
            if not isinstance(aspects, dict):
                return False
            return bool(set(aspects.keys()) & set(aspect_filter))

        filtered = filtered[filtered["aspects"].apply(has_selected_aspect)]

    st.subheader(f"Comments ({len(filtered)})")

    display_df = filtered.copy()

    if not reveal_toxic and "is_toxic" in display_df:
        display_df.loc[display_df["is_toxic"] == True, "text"] = "🔒 Toxic comment hidden — enable reveal to view"

    preferred_columns = [
        "text",
        "sentiment",
        "sentiment_score",
        "emotion",
        "emotion_score",
        "toxicity_label",
        "toxicity_score",
        "aspect_summary",
        "likes",
        "source",
    ]

    display_columns = [c for c in preferred_columns if c in display_df.columns]
    st.dataframe(
        display_df[display_columns],
        width="stretch",
        hide_index=True,
        height=420,
    )

# -----------------------------
# Report tab
# -----------------------------
with tab_report:
    st.subheader("Download Analysis Report")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    raw_name = str(metadata.get("url") or metadata.get("dataset") or metadata.get("filename") or "commentsense")
    file_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", raw_name)[:40]

    c1, c2, c3 = st.columns(3)

    with c1:
        st.download_button(
            label="⬇️ Download CSV",
            data=export_csv(df),
            file_name=f"{file_stem}_{stamp}_analysis.csv",
            mime="text/csv",
            width="stretch",
        )

    with c2:
        st.download_button(
            label="⬇️ Download JSON",
            data=export_json(df, metadata, summary),
            file_name=f"{file_stem}_{stamp}_report.json",
            mime="application/json",
            width="stretch",
        )

    with c3:
        pdf_bytes = export_pdf_report(df, metadata, summary)
        if pdf_bytes:
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_bytes,
                file_name=f"{file_stem}_{stamp}_report.pdf",
                mime="application/pdf",
                width="stretch",
            )
        else:
            st.caption("PDF export needs `reportlab`. Install requirements to enable it.")

    st.divider()
    st.markdown("### Metadata")
    st.json(metadata)