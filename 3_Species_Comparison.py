"""
pages/3_Species_Comparison.py
Side-by-side species comparison tool.
"""

import streamlit as st

st.set_page_config(page_title="AlgoID Compare", page_icon="⚖️", layout="wide")

st.title("⚖️ Species Comparison")
st.caption("Select two genera to compare morphology, ecology, biochemistry, and taxonomy.")

from modules.db_connector import get_all_species, _get_conn
import sqlite3

all_sp = [s["name"] for s in get_all_species()]

col_a, col_b = st.columns(2)
with col_a:
    sp_a = st.selectbox("Species A", all_sp, index=0)
with col_b:
    sp_b = st.selectbox("Species B", all_sp, index=min(1, len(all_sp)-1))

if sp_a == sp_b:
    st.warning("Select two different species to compare.")
    st.stop()

import json
from pathlib import Path

RULES_PATH = Path("data/morphology_rules.json")
with open(RULES_PATH) as f:
    rules = json.load(f)

conn = _get_conn()

def get_db(name):
    row = conn.execute("SELECT * FROM species_cache WHERE name=?", (name,)).fetchone()
    return dict(row) if row else {}

def get_rule(name):
    return rules.get(name, {})

db_a, db_b = get_db(sp_a), get_db(sp_b)
rule_a, rule_b = get_rule(sp_a), get_rule(sp_b)
conn.close()

st.divider()

# ── Taxonomy comparison ───────────────────────────────────────────────────────
st.markdown("### 🌿 Taxonomy")
tax_fields = [
    ("Scientific name", "scientific_name"),
    ("Kingdom", "kingdom"),
    ("Phylum", "phylum"),
    ("Class", "class_"),
    ("Order", "order_"),
    ("Family", "family"),
]
col1, col2, col3 = st.columns([2, 3, 3])
col1.markdown("**Field**")
col2.markdown(f"**{sp_a}**")
col3.markdown(f"**{sp_b}**")
for label, key in tax_fields:
    va, vb = db_a.get(key, "—"), db_b.get(key, "—")
    match = "✅" if va == vb and va != "—" else ("❌" if va != vb else "—")
    col1.write(label)
    col2.write(va or "—")
    col3.write(f"{vb or '—'}  {match}")

st.divider()

# ── Morphology comparison ─────────────────────────────────────────────────────
st.markdown("### 🔬 Morphology")
morph_fields = [
    ("Shape(s)", lambda r: ", ".join(r.get("shape", []))),
    ("Pigmentation", lambda r: ", ".join(r.get("pigmentation", []))),
    ("Motility", lambda r: "✅ Yes" if r.get("motility") else "❌ No"),
    ("Special structures", lambda r: ", ".join(r.get("special_structures", [])) or "None"),
    ("Division", lambda r: r.get("division", "—")),
]
col1, col2, col3 = st.columns([2, 3, 3])
col1.markdown("**Feature**")
col2.markdown(f"**{sp_a}**")
col3.markdown(f"**{sp_b}**")
for label, fn in morph_fields:
    va, vb = fn(rule_a), fn(rule_b)
    col1.write(label)
    col2.write(va)
    col3.write(vb)

st.divider()

# ── Ecology & risk comparison ─────────────────────────────────────────────────
st.markdown("### 🌊 Ecology & Risk")
eco_col1, eco_col2 = st.columns(2)
with eco_col1:
    st.markdown(f"**{sp_a}**")
    st.write(f"Habitat: {db_a.get('habitat','—')}")
    st.write(f"Toxicity: {db_a.get('toxicity','—')}")
    st.write(f"Bloom risk: {db_a.get('bloom_risk','—')}")
with eco_col2:
    st.markdown(f"**{sp_b}**")
    st.write(f"Habitat: {db_b.get('habitat','—')}")
    st.write(f"Toxicity: {db_b.get('toxicity','—')}")
    st.write(f"Bloom risk: {db_b.get('bloom_risk','—')}")

st.divider()

# ── Biochemistry comparison ───────────────────────────────────────────────────
st.markdown("### ⚗️ Biochemical Relevance")
bc1, bc2 = st.columns(2)
bc1.markdown(f"**{sp_a}**")
bc1.write(db_a.get("biochemical", rule_a.get("biochemical","—")))
bc2.markdown(f"**{sp_b}**")
bc2.write(db_b.get("biochemical", rule_b.get("biochemical","—")))

st.divider()

# ── Reference images ──────────────────────────────────────────────────────────
st.markdown("### 📷 Reference Images")
img1, img2 = st.columns(2)
with img1:
    if db_a.get("image_url"):
        st.image(db_a["image_url"], caption=db_a.get("scientific_name",""), width=280)
    else:
        st.info(f"No reference image for {sp_a}")
with img2:
    if db_b.get("image_url"):
        st.image(db_b["image_url"], caption=db_b.get("scientific_name",""), width=280)
    else:
        st.info(f"No reference image for {sp_b}")

# ── External links ────────────────────────────────────────────────────────────
st.divider()
st.markdown("### 🔗 External Links")
lk1, lk2 = st.columns(2)
with lk1:
    st.markdown(f"**{sp_a}**")
    if db_a.get("gbif_id"):
        st.markdown(f"[GBIF](https://www.gbif.org/species/{db_a['gbif_id']})")
    if db_a.get("ncbi_id"):
        st.markdown(f"[NCBI](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={db_a['ncbi_id']})")
    if db_a.get("reference_url"):
        st.markdown(f"[AlgaeBase]({db_a['reference_url']})")
with lk2:
    st.markdown(f"**{sp_b}**")
    if db_b.get("gbif_id"):
        st.markdown(f"[GBIF](https://www.gbif.org/species/{db_b['gbif_id']})")
    if db_b.get("ncbi_id"):
        st.markdown(f"[NCBI](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={db_b['ncbi_id']})")
    if db_b.get("reference_url"):
        st.markdown(f"[AlgaeBase]({db_b['reference_url']})")
