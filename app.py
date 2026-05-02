"""
app.py — AlgoID Intelligent Algae Identification System
Run: streamlit run app.py
"""

import uuid
import json
import tempfile
import streamlit as st
from pathlib import Path
from PIL import Image
from modules.microscope_check import is_microscopic  # ✅ corrected import

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

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔬 AlgoID – Intelligent Algae Identification System")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧬 Morphological Features")

    shape = st.selectbox("Shape", ["unicellular", "colonial", "filamentous", "spiral"])
    pigmentation = st.selectbox("Pigmentation", ["green", "blue-green", "brown"])
    motility = st.checkbox("Motility present")
    structures = st.multiselect(
        "Special structures",
        ["heterocyst", "akinetes", "spiral_chloroplast", "flagella", "gas_vesicles"],
    )

    morph_weight = st.slider("Morphology weight", 0.0, 1.0, 0.45)
    image_weight = 1.0 - morph_weight

    run_btn = st.button("🔍 Identify")

morph_input = {
    "shape": shape,
    "pigmentation": pigmentation,
    "motility": motility,
    "special_structures": structures,
}

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_identify, tab_database, tab_about = st.tabs(
    ["🔬 Identify", "📚 Species Database", "ℹ️ About"]
)

# ─────────────────────────────────────────────────────────────────────────────
with tab_identify:
    col_img, col_morph = st.columns(2)

    # ── IMAGE SECTION (FIXED) ─────────────────────────────────────────────────
    with col_img:
        st.subheader("Microscope Image")

        uploaded = st.file_uploader(
            "Upload microscopy image",
            type=["jpg", "jpeg", "png", "tiff", "bmp"]
        )

        pil_image = None
        image_preds = []

        if uploaded:
            pil_image = Image.open(uploaded)
            st.image(pil_image, use_container_width=True)

            # ✅ Save temp file safely
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                pil_image.save(tmp.name)
                temp_path = tmp.name

            # ✅ Microscopic validation
            is_valid, msg = is_microscopic(temp_path)
            st.info(msg)

            if not is_valid:
                st.error("⚠️ Not a microscopic image")
                st.stop()

            # ✅ CNN prediction
            with st.spinner("Running CNN classifier..."):
                try:
                    from modules.image_classifier import predict_from_image
                    image_preds = predict_from_image(pil_image, top_n=3)
                except Exception as e:
                    st.warning(f"Model error: {e}")
                    image_preds = []

            # ✅ Display predictions
            if image_preds:
                st.markdown("### CNN Predictions")
                for p in image_preds:
                    pct = p["confidence"] * 100
                    st.write(f"{p['species']} — {pct:.1f}%")

        else:
            st.info("Upload image to enable AI prediction")

    # ── MORPHOLOGY SECTION ────────────────────────────────────────────────────
    with col_morph:
        st.subheader("Morphology Scoring")

        from modules.morphology_engine import identify_from_morphology
        morph_preds = identify_from_morphology(morph_input, top_n=5)

        for m in morph_preds:
            pct = m["confidence"] * 100
            st.write(f"{m['genus']} — {pct:.1f}%")

    # ── HYBRID RESULT ─────────────────────────────────────────────────────────
    if run_btn:
        with st.spinner("Running hybrid model..."):
            from modules.hybrid_engine import fuse_predictions, final_prediction

            fused = fuse_predictions(morph_preds, image_preds, morph_weight, image_weight)
            result = final_prediction(fused)

            st.success(f"🦠 Identified: {result['organism']}")
            st.write(f"Confidence: {result['confidence']*100:.2f}%")

# ─────────────────────────────────────────────────────────────────────────────
with tab_database:
    st.write("Database view coming soon...")

# ─────────────────────────────────────────────────────────────────────────────
with tab_about:
    st.write("AlgoID: Hybrid algae identification system.")
