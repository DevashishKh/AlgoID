"""
pages/2_Batch_Identification.py
Streamlit page — upload multiple images or a CSV of morphological data
and receive a downloadable identification report for all samples.
"""

import io
import csv
import json
import uuid
import time
import streamlit as st
from PIL import Image
from pathlib import Path

st.set_page_config(page_title="AlgoID Batch", page_icon="📂", layout="wide")

st.title("📂 Batch Identification")
st.caption("Identify multiple samples at once. Upload images OR a morphology CSV.")

# ── Helpers ───────────────────────────────────────────────────────────────────

def run_morph(row: dict) -> dict:
    from modules.morphology_engine import identify_from_morphology
    structs = [s.strip() for s in row.get("special_structures", "").split("|") if s.strip()]
    inp = {
        "shape": row.get("shape", "unicellular"),
        "pigmentation": row.get("pigmentation", "green"),
        "motility": str(row.get("motility", "false")).lower() in ("true", "1", "yes"),
        "special_structures": structs,
    }
    preds = identify_from_morphology(inp, top_n=3)
    return preds, inp


def run_image(pil_img: Image.Image) -> list:
    try:
        from modules.image_classifier import predict_from_image
        return predict_from_image(pil_img, top_n=3)
    except Exception:
        return []


def fuse(morph_preds, img_preds):
    from modules.hybrid_engine import fuse_predictions, final_prediction
    fused = fuse_predictions(morph_preds, img_preds)
    return final_prediction(fused)


def db_lookup(organism: str) -> dict:
    try:
        from modules.db_connector import get_species_info
        return get_species_info(organism)
    except Exception:
        return {}


# ── Mode selector ─────────────────────────────────────────────────────────────
mode = st.radio(
    "Input mode",
    ["Multiple images", "Morphology CSV"],
    horizontal=True,
)

# ─────────────────────────────────────────────────────────────────────────────
if mode == "Multiple images":
    st.markdown("### Upload microscope images")
    st.caption("Each file is treated as one sample. Filename becomes the sample ID.")

    uploaded_files = st.file_uploader(
        "Choose images",
        type=["jpg", "jpeg", "png", "tiff", "bmp"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        st.info(f"{len(uploaded_files)} image(s) queued.")

        if st.button("▶ Run batch identification"):
            results_table = []
            progress = st.progress(0, text="Processing…")

            for i, f in enumerate(uploaded_files):
                pil_img = Image.open(f)
                img_preds = run_image(pil_img)
                final = fuse([], img_preds)
                db = db_lookup(final["organism"])

                results_table.append({
                    "Sample": f.name,
                    "Predicted": final["organism"],
                    "Scientific name": db.get("scientific_name", ""),
                    "Confidence": f"{final['confidence']*100:.1f}%",
                    "Certainty": final["certainty"],
                    "Phylum": db.get("phylum", ""),
                    "Toxicity": db.get("toxicity", ""),
                    "Bloom risk": db.get("bloom_risk", ""),
                    "GBIF ID": db.get("gbif_id", ""),
                })
                progress.progress((i + 1) / len(uploaded_files),
                                  text=f"Processed {i+1}/{len(uploaded_files)}: {f.name}")
                time.sleep(0.05)

            st.success("Batch complete!")
            st.dataframe(results_table, use_container_width=True)

            # Download CSV
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=results_table[0].keys())
            writer.writeheader()
            writer.writerows(results_table)
            st.download_button(
                "⬇ Download results CSV",
                data=buf.getvalue(),
                file_name=f"AlgoID_batch_{uuid.uuid4().hex[:6]}.csv",
                mime="text/csv",
            )

# ─────────────────────────────────────────────────────────────────────────────
else:  # Morphology CSV
    st.markdown("### Upload morphology CSV")

    st.markdown("""
Expected CSV columns:

| sample_id | shape | pigmentation | motility | special_structures |
|-----------|-------|--------------|----------|--------------------|
| S001 | filamentous | blue-green | false | heterocyst-akinetes |
| S002 | unicellular | green | true | flagella |

`special_structures` — pipe-separated, e.g. `heterocyst|akinetes`
""")

    csv_file = st.file_uploader("Upload CSV", type=["csv"])

    # Sample download
    sample_csv = (
        "sample_id,shape,pigmentation,motility,special_structures\n"
        "S001,filamentous,blue-green,false,heterocyst|akinetes\n"
        "S002,unicellular,green,true,flagella\n"
        "S003,colonial,green,false,\n"
        "S004,filamentous,green,false,spiral_chloroplast\n"
    )
    st.download_button(
        "⬇ Download sample CSV template",
        data=sample_csv,
        file_name="AlgoID_template.csv",
        mime="text/csv",
    )

    if csv_file:
        reader = csv.DictReader(io.StringIO(csv_file.read().decode("utf-8")))
        rows = list(reader)
        st.info(f"{len(rows)} sample(s) found in CSV.")

        if st.button("▶ Run batch identification"):
            results_table = []
            progress = st.progress(0, text="Processing…")

            for i, row in enumerate(rows):
                morph_preds, morph_inp = run_morph(row)
                final = fuse(morph_preds, [])
                db = db_lookup(final["organism"])

                results_table.append({
                    "Sample ID": row.get("sample_id", f"S{i+1:03d}"),
                    "Input shape": morph_inp["shape"],
                    "Input pigment": morph_inp["pigmentation"],
                    "Predicted": final["organism"],
                    "Scientific name": db.get("scientific_name", ""),
                    "Confidence": f"{final['confidence']*100:.1f}%",
                    "Certainty": final["certainty"],
                    "Phylum": db.get("phylum", ""),
                    "Toxicity": db.get("toxicity", ""),
                    "Bloom risk": db.get("bloom_risk", ""),
                    "Habitat": db.get("habitat", ""),
                })
                progress.progress((i + 1) / len(rows))

            st.success("Batch complete!")
            st.dataframe(results_table, use_container_width=True)

            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=results_table[0].keys())
            writer.writeheader()
            writer.writerows(results_table)
            st.download_button(
                "⬇ Download results CSV",
                data=buf.getvalue(),
                file_name=f"AlgoID_morphbatch_{uuid.uuid4().hex[:6]}.csv",
                mime="text/csv",
            )
