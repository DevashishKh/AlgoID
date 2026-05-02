"""
pages/1_Analytics_Dashboard.py
Streamlit page — identification history, accuracy stats, feedback log.
Access via the Streamlit sidebar when running app.py.
"""

import sqlite3
import json
from pathlib import Path
import streamlit as st

DB_PATH = Path("data/sqlite_cache.db")

st.set_page_config(page_title="AlgoID Analytics", page_icon="📊", layout="wide")

st.markdown("""
<style>
.section-title {
    font-size: 1.1rem; font-weight: 700; color: #1a5276;
    border-bottom: 2px solid #1a5276; padding-bottom: 4px; margin: 1rem 0 0.6rem;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 AlgoID — Analytics Dashboard")


def get_conn():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


conn = get_conn()
if conn is None:
    st.error("Database not found. Run `python database_setup.py` first.")
    st.stop()

# ── KPI row ───────────────────────────────────────────────────────────────────
logs = conn.execute("SELECT * FROM identification_log ORDER BY timestamp DESC").fetchall()
feedbacks = conn.execute("SELECT * FROM feedback").fetchall()

total = len(logs)
with_image = sum(1 for r in logs if r["image_used"])
correct_fb = sum(1 for r in feedbacks if r["is_correct"])
accuracy = (correct_fb / len(feedbacks) * 100) if feedbacks else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total identifications", total)
k2.metric("With image input", with_image, delta=f"{with_image/total*100:.0f}%" if total else "0%")
k3.metric("User feedback items", len(feedbacks))
k4.metric("Reported accuracy", f"{accuracy:.1f}%" if feedbacks else "—")

st.divider()

# ── Prediction distribution ───────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<div class="section-title">Most-predicted genera</div>', unsafe_allow_html=True)
    genus_counts: dict = {}
    for r in logs:
        g = r["predicted_genus"] or "Unknown"
        genus_counts[g] = genus_counts.get(g, 0) + 1

    if genus_counts:
        sorted_gc = sorted(genus_counts.items(), key=lambda x: x[1], reverse=True)
        max_count = sorted_gc[0][1]
        for genus, count in sorted_gc:
            pct = count / max_count
            bar = "█" * int(pct * 30)
            st.markdown(
                f"`{genus:<22}` {bar} **{count}**",
                unsafe_allow_html=False,
            )
    else:
        st.info("No identifications recorded yet.")

with col_right:
    st.markdown('<div class="section-title">Certainty distribution</div>', unsafe_allow_html=True)
    certainty_counts: dict = {"High": 0, "Medium": 0, "Low": 0}
    for r in logs:
        c = r["certainty"] or "Low"
        certainty_counts[c] = certainty_counts.get(c, 0) + 1

    colors = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
    for level, count in certainty_counts.items():
        pct = count / total * 100 if total else 0
        st.markdown(f"{colors[level]} **{level}** — {count} runs ({pct:.0f}%)")

    st.divider()
    st.markdown('<div class="section-title">Average confidence by genus</div>',
                unsafe_allow_html=True)
    avg_conf: dict = {}
    for r in logs:
        g = r["predicted_genus"] or "Unknown"
        avg_conf.setdefault(g, []).append(r["confidence"] or 0)

    for g, vals in sorted(avg_conf.items()):
        avg = sum(vals) / len(vals)
        st.markdown(f"**{g}** — {avg*100:.1f}%")

# ── Recent identifications table ──────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-title">Recent identification log</div>', unsafe_allow_html=True)

limit = st.slider("Show last N runs", 5, 100, 20)
recent = conn.execute(
    "SELECT * FROM identification_log ORDER BY timestamp DESC LIMIT ?", (limit,)
).fetchall()

if recent:
    rows_display = []
    for r in recent:
        morph = json.loads(r["morph_input"] or "{}")
        rows_display.append({
            "Timestamp": r["timestamp"],
            "Session": r["session_id"],
            "Predicted": r["predicted_genus"],
            "Confidence": f"{(r['confidence'] or 0)*100:.1f}%",
            "Certainty": r["certainty"],
            "Image used": "✅" if r["image_used"] else "❌",
            "Shape": morph.get("shape", ""),
            "Pigment": morph.get("pigmentation", ""),
        })
    st.dataframe(rows_display, use_container_width=True)
else:
    st.info("No runs recorded yet.")

# ── Feedback log ──────────────────────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-title">User feedback log</div>', unsafe_allow_html=True)

if feedbacks:
    fb_rows = []
    for r in feedbacks:
        fb_rows.append({
            "Timestamp": r["timestamp"],
            "Predicted": r["predicted_genus"],
            "Actual": r["actual_genus"],
            "Correct": "✅" if r["is_correct"] else "❌",
            "Notes": r["notes"],
        })
    st.dataframe(fb_rows, use_container_width=True)

    # Confusion summary
    st.markdown('<div class="section-title">Prediction errors</div>', unsafe_allow_html=True)
    wrong = [(r["predicted_genus"], r["actual_genus"])
             for r in feedbacks if not r["is_correct"] and r["actual_genus"]]
    if wrong:
        for pred, actual in wrong:
            st.markdown(f"• Predicted **{pred}** → actual **{actual}**")
    else:
        st.success("No confirmed errors in feedback log.")
else:
    st.info("No feedback submitted yet.")

conn.close()
