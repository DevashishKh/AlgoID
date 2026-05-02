"""
modules/db_connector.py
Fetches taxonomic data from GBIF and NCBI, with SQLite caching.
Falls back to seeded local data when APIs are unavailable.
"""

import sqlite3
import json
import time
from pathlib import Path

import os as _os
DB_PATH = Path(_os.environ.get("ALGOID_DB_PATH",
               str(Path(__file__).parent.parent / "data" / "sqlite_cache.db")))

try:
    import requests
    _requests_available = True
except ImportError:
    _requests_available = False


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row) -> dict:
    return dict(row) if row else {}


def fetch_gbif(species_name: str) -> dict:
    """Query GBIF Species Match API — free, no key required."""
    if not _requests_available:
        return {}
    try:
        url = "https://api.gbif.org/v1/species/match"
        resp = requests.get(
            url,
            params={"name": species_name, "verbose": "false"},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("matchType") == "NONE":
            return {}
        return {
            "scientific_name": data.get("scientificName", species_name),
            "kingdom": data.get("kingdom", ""),
            "phylum": data.get("phylum", ""),
            "class_": data.get("class", ""),
            "order_": data.get("order", ""),
            "family": data.get("family", ""),
            "gbif_id": str(data.get("usageKey", "")),
        }
    except Exception as e:
        print(f"GBIF fetch error for '{species_name}': {e}")
        return {}


def fetch_ncbi_taxid(species_name: str) -> str:
    """Look up NCBI Taxonomy ID via E-utilities — free."""
    if not _requests_available:
        return ""
    try:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        resp = requests.get(
            url,
            params={"db": "taxonomy", "term": species_name, "retmode": "json"},
            timeout=8,
        )
        resp.raise_for_status()
        ids = resp.json().get("esearchresult", {}).get("idlist", [])
        return ids[0] if ids else ""
    except Exception as e:
        print(f"NCBI fetch error for '{species_name}': {e}")
        return ""


def get_species_info(species_name: str, force_refresh: bool = False) -> dict:
    """
    Return full taxonomic record for a species name.
    Order of priority:
      1. SQLite cache (unless force_refresh=True)
      2. Live GBIF + NCBI API fetch
      3. Minimal fallback record
    """
    conn = _get_conn()

    if not force_refresh:
        row = conn.execute(
            "SELECT * FROM species_cache WHERE name=?", (species_name,)
        ).fetchone()
        if row:
            conn.close()
            return _row_to_dict(row)

    # Live fetch
    gbif = fetch_gbif(species_name)
    ncbi_id = fetch_ncbi_taxid(species_name)
    time.sleep(0.3)  # polite rate-limiting

    info = {
        "name": species_name,
        "scientific_name": gbif.get("scientific_name", species_name),
        "kingdom": gbif.get("kingdom", ""),
        "phylum": gbif.get("phylum", ""),
        "class_": gbif.get("class_", ""),
        "order_": gbif.get("order_", ""),
        "family": gbif.get("family", ""),
        "habitat": "",
        "biochemical": "",
        "gbif_id": gbif.get("gbif_id", ""),
        "ncbi_id": ncbi_id,
        "image_url": "",
        "toxicity": "",
        "bloom_risk": "",
        "reference_url": (
            f"https://www.gbif.org/species/{gbif['gbif_id']}"
            if gbif.get("gbif_id") else ""
        ),
    }

    # Upsert into cache
    conn.execute("""
        INSERT OR REPLACE INTO species_cache
        (name, scientific_name, kingdom, phylum, class_, order_, family,
         habitat, biochemical, gbif_id, ncbi_id, image_url,
         toxicity, bloom_risk, reference_url)
        VALUES
        (:name,:scientific_name,:kingdom,:phylum,:class_,:order_,:family,
         :habitat,:biochemical,:gbif_id,:ncbi_id,:image_url,
         :toxicity,:bloom_risk,:reference_url)
    """, info)
    conn.commit()
    conn.close()
    return info


def log_identification(session_id: str, result: dict, morph_input: dict, image_used: bool):
    """Record each identification run for analytics."""
    conn = _get_conn()
    conn.execute("""
        INSERT INTO identification_log
        (session_id, predicted_genus, confidence, certainty, morph_input, image_used)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        result.get("organism", ""),
        result.get("confidence", 0.0),
        result.get("certainty", ""),
        json.dumps(morph_input),
        int(image_used),
    ))
    conn.commit()
    conn.close()


def log_feedback(session_id: str, predicted: str, actual: str, correct: bool, notes: str = ""):
    """Store user-provided accuracy feedback."""
    conn = _get_conn()
    conn.execute("""
        INSERT INTO feedback (session_id, predicted_genus, actual_genus, is_correct, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, predicted, actual, int(correct), notes))
    conn.commit()
    conn.close()


def get_all_species() -> list:
    """Return all species in local cache (for dropdowns / search)."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT name, scientific_name, phylum FROM species_cache ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
