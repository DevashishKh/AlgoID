"""
modules/hybrid_engine.py
Weighted fusion of morphology and image predictions.
"""


def fuse_predictions(
    morphology_results: list,
    image_results: list,
    morph_weight: float = 0.45,
    image_weight: float = 0.55,
) -> list:
    """
    Combine morphology rule scores and CNN probabilities.
    Returns a merged candidate list sorted by fused confidence.

    - morph_weight + image_weight should sum to 1.0
    - If only one input source is available, full weight is applied to that source.
    """
    # Normalise weights if only one source is active
    has_morph = bool(morphology_results)
    has_image = bool(image_results)

    if has_morph and not has_image:
        morph_weight, image_weight = 1.0, 0.0
    elif has_image and not has_morph:
        morph_weight, image_weight = 0.0, 1.0

    scores: dict = {}

    for r in morphology_results:
        name = r["genus"]
        scores.setdefault(name, {"score": 0.0, "habitat": r.get("habitat", ""),
                                  "biochemical": r.get("biochemical", ""),
                                  "division": r.get("division", "")})
        scores[name]["score"] += r["confidence"] * morph_weight

    for r in image_results:
        name = r["species"]
        scores.setdefault(name, {"score": 0.0, "habitat": "", "biochemical": "", "division": ""})
        scores[name]["score"] += r["confidence"] * image_weight

    fused = [
        {
            "organism": k,
            "fused_confidence": round(min(v["score"], 1.0), 4),
            "habitat": v["habitat"],
            "biochemical": v["biochemical"],
            "division": v["division"],
        }
        for k, v in scores.items()
    ]
    fused.sort(key=lambda x: x["fused_confidence"], reverse=True)
    return fused


def final_prediction(fused: list) -> dict:
    """
    Return the top prediction with certainty label and alternatives.
    """
    if not fused:
        return {
            "organism": "Unidentified",
            "confidence": 0.0,
            "certainty": "low",
            "certainty_color": "red",
            "alternatives": [],
            "habitat": "",
            "biochemical": "",
            "division": "",
        }
    top = fused[0]
    score = top["fused_confidence"]
    if score >= 0.75:
        certainty, color = "High", "green"
    elif score >= 0.45:
        certainty, color = "Medium", "orange"
    else:
        certainty, color = "Low", "red"

    return {
        "organism": top["organism"],
        "confidence": score,
        "certainty": certainty,
        "certainty_color": color,
        "alternatives": fused[1:4],
        "habitat": top.get("habitat", ""),
        "biochemical": top.get("biochemical", ""),
        "division": top.get("division", ""),
    }
