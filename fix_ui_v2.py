# fix_ui_v2.py  ->  Steps 3-9 ka automatic patch
from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")
log = []

# ---------- PART A: CSS classes ensure karo (summary-card, alerts, metric fix) ----------
ADD_CSS = '''
    /* FIX PACK v2 additions */
    [data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        font-weight: 800 !important;
        overflow: visible !important;
        text-overflow: clip !important;
        white-space: normal !important;
    }
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
'''
if ".summary-card {" not in s:
    idx = s.find("</style>")
    if idx != -1:
        s = s[:idx] + ADD_CSS + s[idx:]
        log.append("CSS classes add hui (summary-card, alert colors, metric truncation fix)")
    else:
        log.append("WARNING: </style> nahi mila - CSS skip hua")
else:
    log.append("CSS pehle se maujood hai")

# ---------- PART B: chhote string fixes (Step 3 ke bache hue) ----------
if 'm2.metric("Brand Health", f"{health}/100")' in s:
    s = s.replace('m2.metric("Brand Health", f"{health}/100")',
                  'm2.metric("Brand Health (/100)", f"{health:.0f}")')
    log.append("Brand Health metric fix hua")
else:
    log.append("Brand Health metric skip (pehle se theek ya alag format)")

for old, new in [
    ('progress_text.text("Analysis complete ✅")', 'progress_text.empty()'),
    ('bar.progress(1.0, text="Analysis complete ✅")', 'bar.empty()'),
]:
    if old in s:
        s = s.replace(old, new)
        log.append("Stray 'Analysis complete' line hatayi")
        break

anchor = 'm7.metric("Top Emotion", str(top_emotion).title())'
if anchor in s and "Low sample size" not in s:
    warn = anchor + '''
if len(df) < 30:
    st.warning(
        f"⚠️ Low sample size: sirf {len(df)} comments mile. "
        "Insights ki statistical confidence kam hogi — fetch amount badhao ya koi active post try karo."
    )'''
    s = s.replace(anchor, warn, 1)
    log.append("Low-sample warning add hui")
else:
    log.append("Low-sample warning skip")

# ---------- PART C: POORA Insights tab section replace (Steps 4-9) ----------
NEW_BLOCK = '''with tab_insights:

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
'''

START = "with tab_insights:"
END_MARK = "# Comment Explorer tab"
i = s.find(START)
j = s.find(END_MARK)
if i == -1 or j == -1:
    print("❌ ERROR: app.py mein markers nahi mile:")
    print("   'with tab_insights:' mila?", i != -1)
    print("   '# Comment Explorer tab' mila?", j != -1)
    print("   File mein kuch nahi badla. Safe hai.")
    raise SystemExit(1)

k = s.rfind("# ----", i, j)
if k == -1:
    k = j
s = s[:i] + NEW_BLOCK + "\n\n" + s[k:]
log.append("POORA Insights tab section replace hua (Steps 4-9 ek saath)")

p.write_text(s, encoding="utf-8")
print("✅ app.py update ho gaya:")
for line in log:
    print("   -", line)