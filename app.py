"""
app.py — AlgoID Intelligent Algae Identification System
Run: streamlit run app.py
"""

import uuid
import json
import streamlit as st
from pathlib import Path
from PIL import Image
from microscope_check import is_microscopic

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AlgoID – Algae Identification",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ─────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "result" not in st.session_state:
    st.session_state.result = None
if "report" not in st.session_state:
    st.session_state.report = None

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #1a5276, #117a65);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 1.5rem;
}
.main-header h1 { color: white; margin: 0; font-size: 2rem; }
.main-header p  { color: #a9dfbf; margin: 0.3rem 0 0; font-size: 1rem; }

.result-card {
    background: #eafaf1;
    border: 1px solid #27ae60;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin: 1rem 0;
}
.result-card-warn {
    background: #fef9e7;
    border: 1px solid #f39c12;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin: 1rem 0;
}
.result-card-danger {
    background: #fdedec;
    border: 1px solid #e74c3c;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin: 1rem 0;
}
.tax-badge {
    display: inline-block;
    background: #d5e8d4;
    color: #1e8449;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.82rem;
    margin: 2px;
    font-weight: 600;
}
.confidence-bar {
    background: #d5d8dc;
    border-radius: 6px;
    height: 10px;
    margin: 4px 0 8px;
}
.confidence-fill {
    background: #27ae60;
    border-radius: 6px;
    height: 10px;
}
.section-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1a5276;
    border-bottom: 2px solid #1a5276;
    padding-bottom: 4px;
    margin: 1.2rem 0 0.8rem;
}
.stButton > button {
    background: #117a65;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.5rem;
    font-weight: 600;
    font-size: 1rem;
}
.stButton > button:hover { background: #0e6655; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🔬 AlgoID – Intelligent Algae Identification System</h1>
  <p>Hybrid morphology + AI image classification · GBIF · NCBI · AlgaeBase integration</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar: Morphological Input ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧬 Morphological Features")
    st.caption(f"Session: `{st.session_state.session_id}`")
    st.divider()

    shape = st.selectbox(
        "Cell / colony shape",
        ["unicellular", "colonial", "filamentous", "spiral"],
        help="Overall morphological form observed under microscope"
    )
    pigmentation = st.selectbox(
        "Pigmentation",
        ["green", "blue-green", "brown"],
        help="Dominant colour of the sample"
    )
    motility = st.checkbox(
        "Motility present (flagella observed)",
        help="Check if the cells appear to be actively moving"
    )
    structures = st.multiselect(
        "Special structures observed",
        ["heterocyst", "akinetes", "spiral_chloroplast",
         "flagella", "gas_vesicles"],
        help="Select any distinctive structures visible"
    )

    st.divider()
    morph_weight = st.slider(
        "Morphology weight",
        0.0, 1.0, 0.45, 0.05,
        help="Relative weight given to morphology in hybrid scoring"
    )
    image_weight = round(1.0 - morph_weight, 2)
    st.caption(f"Image weight: **{image_weight}**")

    st.divider()
    run_btn = st.button("🔍 Identify Organism", use_container_width=True)

morph_input = {
    "shape": shape,
    "pigmentation": pigmentation,
    "motility": motility,
    "special_structures": structures,
}

# ── Main area: tabs ───────────────────────────────────────────────────────────
tab_identify, tab_database, tab_about = st.tabs(
    ["🔬 Identify", "📚 Species Database", "ℹ️ About"]
)

# ─────────────────────────────────────────────────────────────────────────────
with tab_identify:
    col_img, col_morph = st.columns([1, 1], gap="medium")

    # Image upload column
    with col_img:
        st.markdown('<div class="section-title">Microscope Image</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Upload microscopy image",
            type=["jpg", "jpeg", "png", "tiff", "bmp"],
            help="JPEG/PNG/TIFF from any light microscope"
        )
        pil_image = None
        image_preds = []

        if uploaded:
            pil_image = Image.open(uploaded)
            st.image(pil_image, caption="Uploaded image", use_container_width=True)
            # Save a temp file because your function needs a path for cv2.imread
    temp_path = "temp_validation_img.jpg"
    pil_image.save(temp_path)
    
    is_valid, msg = is_microscopic(temp_path)
    
    if not is_valid:
        st.error(f"⚠️ **Microscopy Check Failed:** {msg}")
        st.stop()  # This prevents the rest of the code from running
    # --- NEW CHECKER CODE ENDS HERE ---

    # --- YOUR CODE CONTINUES (Line 182) ---
    with st.spinner("Running CNN classifier..."):
         try:
             from modules.image_classifier import predict_from_image
             image_preds = predict_from_image(pil_image, top_n=3)
         except Exception as e:
          st.warning(f"Image classifier unavailable: {e}")
          image_preds = []

     st.markdown("**CNN predictions:**")
            for p in image_preds:
                pct = p["confidence"] * 100
                st.markdown(
                    f"**{p['species']}** — {pct:.1f}%<br>"
                    f'<div class="confidence-bar"><div class="confidence-fill" '
                    f'style="width:{pct:.0f}%"></div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("Upload a microscope image for AI-based classification.\n\n"
                    "Morphology-only identification is still available →")

    # Morphology results column
    with col_morph:
        st.markdown('<div class="section-title">Morphology Scoring</div>', unsafe_allow_html=True)

        from modules.morphology_engine import identify_from_morphology
        morph_preds = identify_from_morphology(morph_input, top_n=5)

        if morph_preds:
            for m in morph_preds:
                pct = m["confidence"] * 100
                st.markdown(
                    f"**{m['genus']}** ({m['division']}) — {pct:.1f}%<br>"
                    f'<div class="confidence-bar"><div class="confidence-fill" '
                    f'style="width:{pct:.0f}%; background:#1a5276"></div></div>'
                    f'<small style="color:#666">{m["habitat"][:80]}</small>',
                    unsafe_allow_html=True,
                )
        else:
            st.warning("No candidates matched — try adjusting your morphological inputs.")

    # ── Run hybrid identification ─────────────────────────────────────────────
    st.divider()

    if run_btn or st.session_state.result:
        if run_btn:
            with st.spinner("Running hybrid decision engine…"):
                from modules.hybrid_engine import fuse_predictions, final_prediction
                from modules.db_connector import get_species_info, log_identification
                from utils.result_formatter import build_report

                fused = fuse_predictions(morph_preds, image_preds,
                                         morph_weight, image_weight)
                result = final_prediction(fused)
                db_info = get_species_info(result["organism"])

                report = build_report(result, db_info, morph_preds, image_preds)
                log_identification(
                    st.session_state.session_id, result, morph_input, bool(pil_image)
                )
                st.session_state.result = result
                st.session_state.report = report
                st.session_state.db_info = db_info

        result = st.session_state.result
        report = st.session_state.report
        db_info = st.session_state.get("db_info", {})

        if result:
            card_cls = {
                "High": "result-card",
                "Medium": "result-card-warn",
                "Low": "result-card-danger",
            }.get(result["certainty"], "result-card")

            st.markdown(f"""
<div class="{card_cls}">
  <h2 style="margin:0">🦠 {result['organism']}</h2>
  <p style="margin:4px 0 0;font-size:1.05rem">
    <em>{db_info.get('scientific_name', '')}</em>
  </p>
  <p style="margin:6px 0 0">
    Confidence: <strong>{result['confidence']*100:.1f}%</strong> &nbsp;|&nbsp;
    Certainty: <strong>{result['certainty']}</strong> &nbsp;|&nbsp;
    Division: <strong>{result.get('division') or db_info.get('phylum','')}</strong>
  </p>
</div>
""", unsafe_allow_html=True)

            # Taxonomy
            if any(db_info.get(k) for k in ["kingdom","phylum","class_","order_","family"]):
                st.markdown('<div class="section-title">🌿 Taxonomic Hierarchy</div>',
                            unsafe_allow_html=True)
                cols = st.columns(5)
                for col, (label, key) in zip(
                    cols,
                    [("Kingdom","kingdom"),("Phylum","phylum"),("Class","class_"),
                     ("Order","order_"),("Family","family")]
                ):
                    col.metric(label, db_info.get(key) or "—")

            # Ecology & Biochemistry
            eco_col, bio_col = st.columns(2)
            with eco_col:
                st.markdown('<div class="section-title">🌊 Ecology</div>',
                            unsafe_allow_html=True)
                st.write(db_info.get("habitat") or result.get("habitat") or "—")
                tox = db_info.get("toxicity", "")
                bloom = db_info.get("bloom_risk", "")
                if tox:
                    st.markdown(f"**Toxicity:** {tox}")
                if bloom:
                    colour = "#e74c3c" if "High" in bloom else "#f39c12" if "Medium" in bloom else "#27ae60"
                    st.markdown(
                        f'**Bloom risk:** <span style="color:{colour};font-weight:700">{bloom}</span>',
                        unsafe_allow_html=True
                    )
            with bio_col:
                st.markdown('<div class="section-title">⚗️ Biochemical Relevance</div>',
                            unsafe_allow_html=True)
                st.write(db_info.get("biochemical") or result.get("biochemical") or "—")

            # External links
            st.markdown('<div class="section-title">🔗 Database References</div>',
                        unsafe_allow_html=True)
            link_col1, link_col2, link_col3 = st.columns(3)
            with link_col1:
                if db_info.get("gbif_id"):
                    st.markdown(f"[🌍 View on GBIF](https://www.gbif.org/species/{db_info['gbif_id']})")
            with link_col2:
                if db_info.get("ncbi_id"):
                    st.markdown(
                        f"[🧬 View on NCBI](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={db_info['ncbi_id']})"
                    )
            with link_col3:
                if db_info.get("reference_url"):
                    st.markdown(f"[🔬 AlgaeBase](  {db_info['reference_url']})")

            # Reference image
            if db_info.get("image_url"):
                with st.expander("📷 Reference image"):
                    st.image(db_info["image_url"],
                             caption=f"Reference: {db_info.get('scientific_name','')}",
                             width=320)

            # Alternatives
            if result.get("alternatives"):
                with st.expander("🔄 Alternative candidates"):
                    for alt in result["alternatives"]:
                        st.markdown(
                            f"**{alt['organism']}** — {alt['fused_confidence']*100:.1f}%  \n"
                            f"<small>{alt.get('habitat','')}</small>",
                            unsafe_allow_html=True
                        )

            # Full JSON report download
            st.divider()
            dl_col, fb_col = st.columns(2)
            with dl_col:
                st.download_button(
                    "⬇ Download identification report (JSON)",
                    data=json.dumps(report, indent=2),
                    file_name=f"AlgoID_{report['report_id']}.json",
                    mime="application/json",
                )
            with fb_col:
                with st.expander("✅ Submit feedback"):
                    actual = st.text_input("Actual genus (if known)")
                    correct = st.radio("Was the prediction correct?", ["Yes", "No"])
                    notes = st.text_area("Additional notes")
                    if st.button("Submit"):
                        from modules.db_connector import log_feedback
                        log_feedback(
                            st.session_state.session_id,
                            result["organism"],
                            actual,
                            correct == "Yes",
                            notes,
                        )
                        st.success("Feedback recorded — thank you!")
    else:
        st.info("Set morphological parameters in the sidebar and click **Identify Organism**.")

# ─────────────────────────────────────────────────────────────────────────────
with tab_database:
    st.markdown("## 📚 Local Species Database")
    st.caption("All 12 seeded species with morphological, ecological, and biochemical data.")

    try:
        from modules.db_connector import get_all_species, _get_conn
        species_list = get_all_species()

        search = st.text_input("🔎 Search species", placeholder="e.g. Chlorella, Cyanobacteria…")

        conn = _get_conn()
        all_rows = conn.execute("SELECT * FROM species_cache ORDER BY name").fetchall()
        conn.close()

        for row in all_rows:
            r = dict(row)
            if search and search.lower() not in (r.get("name","") + r.get("scientific_name","") +
               r.get("phylum","") + r.get("kingdom","")).lower():
                continue
            with st.expander(f"🔬 {r['name']}  —  *{r.get('scientific_name','')}*"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Kingdom:** {r.get('kingdom','—')}  \n"
                                f"**Phylum:** {r.get('phylum','—')}  \n"
                                f"**Class:** {r.get('class_','—')}  \n"
                                f"**Order:** {r.get('order_','—')}  \n"
                                f"**Family:** {r.get('family','—')}")
                with c2:
                    st.markdown(f"**Habitat:** {r.get('habitat','—')}  \n"
                                f"**Toxicity:** {r.get('toxicity','—')}  \n"
                                f"**Bloom risk:** {r.get('bloom_risk','—')}  \n"
                                f"**GBIF ID:** {r.get('gbif_id','—')}  \n"
                                f"**NCBI ID:** {r.get('ncbi_id','—')}")
                st.markdown(f"**Biochemical relevance:** {r.get('biochemical','—')}")
                if r.get("reference_url"):
                    st.markdown(f"[🔗 Reference]({r['reference_url']})")
                if r.get("image_url"):
                    st.image(r["image_url"], width=200)

    except Exception as e:
        st.error(f"Database unavailable: {e}\nRun `python database_setup.py` first.")

# ─────────────────────────────────────────────────────────────────────────────
with tab_about:
    st.markdown("""
## About AlgoID

**AlgoID** is a hybrid freshwater microalgae identification system combining:

- **Rule-based morphology engine** — a JSON knowledge base of 12 genera with
  weighted scoring across shape, pigmentation, motility, and special structures.
- **CNN image classifier** — MobileNetV2 fine-tuned on labeled microscopy images
  (TensorFlow / Keras). Falls back gracefully when a trained model is not present.
- **Hybrid decision engine** — configurable weighted fusion of morphology scores
  and CNN probabilities with adjustable sliders.
- **Database integration** — GBIF Species Match API and NCBI E-utilities for live
  taxonomy lookup, with SQLite caching and 12 seeded species records.

### Supported genera (v1.0)
Anabaena · Chlorella · Chlamydomonas · Diatom Navicula · Euglena · Microcystis ·
Nostoc · Oscillatoria · Pediastrum · Spirogyra · Volvox · Zygnema

### How to extend
1. **Add genera** — edit `data/morphology_rules.json` and add a row to `database_setup.py`
2. **Train CNN** — collect images into `data/algae_dataset/<ClassName>/`, then run:
   ```
   python -c "from modules.image_classifier import train_model; train_model()"
   ```
3. **Add datasets** — Kaggle algae microscopy datasets, AlgaeBase image galleries,
   or lab-collected images all work with the ImageFolder layout.

### References
- AlgaeBase: algaebase.org
- GBIF API: api.gbif.org/v1
- NCBI E-utilities: eutils.ncbi.nlm.nih.gov
- MobileNetV2: Sandler et al., 2018

### Version
AlgoID v1.0 · Built with Streamlit · Python 3.10+
""")
