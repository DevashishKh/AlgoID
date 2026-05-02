"""
utils/result_formatter.py
Standardised output schema for AlgoID predictions.
"""
import uuid
from datetime import datetime


def build_report(final: dict, db_info: dict, morph_preds: list, img_preds: list) -> dict:
    """Assemble a complete identification report dictionary."""
    return {
        "report_id": str(uuid.uuid4())[:8].upper(),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "predicted_organism": final.get("organism", "Unknown"),
        "confidence_score": final.get("confidence", 0.0),
        "certainty_level": final.get("certainty", "low"),
        "division": final.get("division") or db_info.get("division", ""),
        "taxonomy": {
            "scientific_name": db_info.get("scientific_name", ""),
            "kingdom": db_info.get("kingdom", ""),
            "phylum": db_info.get("phylum", ""),
            "class": db_info.get("class_", ""),
            "order": db_info.get("order_", ""),
            "family": db_info.get("family", ""),
        },
        "ecology": {
            "habitat": db_info.get("habitat") or final.get("habitat", ""),
            "toxicity": db_info.get("toxicity", ""),
            "bloom_risk": db_info.get("bloom_risk", ""),
        },
        "biochemical_relevance": db_info.get("biochemical") or final.get("biochemical", ""),
        "external_links": {
            "gbif": (
                f"https://www.gbif.org/species/{db_info['gbif_id']}"
                if db_info.get("gbif_id") else ""
            ),
            "ncbi": (
                f"https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={db_info['ncbi_id']}"
                if db_info.get("ncbi_id") else ""
            ),
            "algaebase": db_info.get("reference_url", ""),
        },
        "alternatives": final.get("alternatives", []),
        "morphology_predictions": morph_preds,
        "image_predictions": img_preds,
    }
