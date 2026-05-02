"""
modules/algaebase_scraper.py
Lightweight AlgaeBase scraper — fetches species detail pages and
extracts taxonomic synonyms, distribution, and ecology notes.

Usage:
    from modules.algaebase_scraper import scrape_species
    data = scrape_species("Chlorella vulgaris")

AlgaeBase does not provide a public REST API, so this module
uses requests + html.parser (stdlib) to parse species detail pages.
Respects a polite delay between requests.
"""

import re
import time
from html.parser import HTMLParser

try:
    import requests
    _requests_ok = True
except ImportError:
    _requests_ok = False

SEARCH_URL = "https://www.algaebase.org/search/species/"
DETAIL_URL = "https://www.algaebase.org/search/species/detail/"
HEADERS = {
    "User-Agent": (
        "AlgoID-Research-Bot/1.0 "
        "(educational algae identification project; "
        "contact: your@email.com)"
    )
}
POLITE_DELAY = 2.0  # seconds between requests


class _TableParser(HTMLParser):
    """Minimal parser that extracts <td> text from AlgaeBase detail pages."""

    def __init__(self):
        super().__init__()
        self.in_td = False
        self.cells: list[str] = []
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self.in_td = True
            self._buf = []

    def handle_endtag(self, tag):
        if tag == "td" and self.in_td:
            self.cells.append(" ".join(self._buf).strip())
            self.in_td = False

    def handle_data(self, data):
        if self.in_td:
            self._buf.append(data.strip())


def _search_species_id(scientific_name: str) -> str | None:
    """Return the AlgaeBase species_id for a given scientific name."""
    if not _requests_ok:
        return None
    try:
        resp = requests.get(
            SEARCH_URL,
            params={"genus": scientific_name.split()[0],
                    "species": scientific_name.split()[1] if " " in scientific_name else ""},
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        # Find first species_id in links
        matches = re.findall(r"species_id=(\d+)", resp.text)
        return matches[0] if matches else None
    except Exception as e:
        print(f"AlgaeBase search error: {e}")
        return None


def _fetch_detail_page(species_id: str) -> dict:
    """Scrape the AlgaeBase species detail page and return a data dict."""
    if not _requests_ok:
        return {}
    try:
        resp = requests.get(
            DETAIL_URL,
            params={"species_id": species_id},
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        html = resp.text

        parser = _TableParser()
        parser.feed(html)
        cells = [c for c in parser.cells if c]

        # Pair consecutive cells as label → value
        data = {}
        for i in range(0, len(cells) - 1, 2):
            label = cells[i].rstrip(":").strip().lower()
            value = cells[i + 1].strip()
            if label and value:
                data[label] = value

        # Extract reference image URL
        img_match = re.search(r'<img[^>]+src="([^"]+algaebase[^"]+\.(jpg|jpeg|png))"', html, re.I)
        if img_match:
            data["image_url"] = img_match.group(1)

        data["algaebase_url"] = f"{DETAIL_URL}?species_id={species_id}"
        data["species_id"] = species_id
        return data

    except Exception as e:
        print(f"AlgaeBase detail fetch error: {e}")
        return {}


def scrape_species(scientific_name: str, species_id: str | None = None) -> dict:
    """
    Main entry point. Pass a scientific name OR a known species_id.
    Returns a dict with keys like: 'habitat', 'distribution', 'synonyms',
    'image_url', 'algaebase_url', 'species_id'.
    """
    if not _requests_ok:
        return {"error": "requests library not installed"}

    sid = species_id or _search_species_id(scientific_name)
    if not sid:
        return {"error": f"Species '{scientific_name}' not found on AlgaeBase"}

    time.sleep(POLITE_DELAY)
    raw = _fetch_detail_page(sid)

    # Normalise common field names
    result = {
        "species_id": sid,
        "algaebase_url": raw.get("algaebase_url", f"{DETAIL_URL}?species_id={sid}"),
        "image_url": raw.get("image_url", ""),
        "habitat": raw.get("habitat", raw.get("ecology", "")),
        "distribution": raw.get("distribution", raw.get("geographic distribution", "")),
        "synonyms": raw.get("synonyms", raw.get("basionym", "")),
        "authority": raw.get("authority", raw.get("taxonomic status", "")),
        "raw": raw,
    }
    return result


# ── Convenience: bulk scrape and update SQLite cache ─────────────────────────
def enrich_database_from_algaebase():
    """
    Iterate over all species in the SQLite cache that have an AlgaeBase
    reference_url and enrich their habitat/image_url fields.
    Call once after initial setup:
        python -c "from modules.algaebase_scraper import enrich_database_from_algaebase; enrich_database_from_algaebase()"
    """
    import sqlite3
    from pathlib import Path

    DB_PATH = Path("data/sqlite_cache.db")
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT name, scientific_name, reference_url FROM species_cache"
    ).fetchall()

    for name, sci_name, ref_url in rows:
        sid = None
        if ref_url:
            m = re.search(r"species_id=(\d+)", ref_url)
            if m:
                sid = m.group(1)
        print(f"Enriching {name} ({sci_name}) …")
        data = scrape_species(sci_name, species_id=sid)
        if "error" not in data:
            conn.execute("""
                UPDATE species_cache
                SET habitat   = COALESCE(NULLIF(:habitat,''), habitat),
                    image_url = COALESCE(NULLIF(:image_url,''), image_url)
                WHERE name = :name
            """, {"habitat": data["habitat"], "image_url": data["image_url"], "name": name})
            conn.commit()
            print(f"  ✓ Updated {name}")
        else:
            print(f"  ✗ {data['error']}")
        time.sleep(POLITE_DELAY)

    conn.close()
    print("AlgaeBase enrichment complete.")


if __name__ == "__main__":
    # Quick test
    result = scrape_species("Chlorella vulgaris", species_id="39143")
    import pprint
    pprint.pprint(result)
