"""
modules/morphology_engine.py
Rule-based scoring engine for morphological identification.
"""

import json
from pathlib import Path

RULES_PATH = Path(__file__).parent.parent / "data" / "morphology_rules.json"


def load_rules() -> dict:
    with open(RULES_PATH) as f:
        return json.load(f)


def score_candidate(candidate: dict, user_input: dict) -> float:
    """
    Score a candidate genus against user morphological features.
    Returns a weighted 0.0–1.0 confidence score.
    """
    score = 0.0
    max_score = 4.0

    # Shape match (weight: 1.0)
    if user_input.get("shape") in candidate.get("shape", []):
        score += 1.0

    # Pigmentation match (weight: 1.0)
    if user_input.get("pigmentation") in candidate.get("pigmentation", []):
        score += 1.0

    # Motility match (weight: 1.0)
    if user_input.get("motility") == candidate.get("motility", False):
        score += 1.0

    # Special structures overlap (weight: 1.0)
    user_structs = set(user_input.get("special_structures", []))
    cand_structs = set(candidate.get("special_structures", []))
    if cand_structs and user_structs:
        overlap = len(user_structs & cand_structs) / len(cand_structs)
        score += overlap
    elif not cand_structs and not user_structs:
        score += 1.0
    elif not cand_structs and user_structs:
        score += 0.5  # partial credit — user sees extra structures

    raw = (score / max_score) * candidate.get("score_weight", 1.0)
    return round(min(raw, 1.0), 4)


def identify_from_morphology(user_input: dict, top_n: int = 5) -> list:
    """
    Match user morphological input against the rules JSON.
    Returns top_n candidates sorted by confidence.
    """
    rules = load_rules()
    results = []
    for genus, candidate in rules.items():
        confidence = score_candidate(candidate, user_input)
        if confidence > 0.1:
            results.append({
                "genus": genus,
                "confidence": confidence,
                "habitat": candidate.get("habitat", ""),
                "biochemical": candidate.get("biochemical", ""),
                "division": candidate.get("division", ""),
            })
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results[:top_n]
