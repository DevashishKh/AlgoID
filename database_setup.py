"""
database_setup.py
Initialises the SQLite database and seeds it with known species records.
Run once: python database_setup.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "sqlite_cache.db"

SEED_DATA = [
    {
        "name": "Chlorella",
        "scientific_name": "Chlorella vulgaris",
        "kingdom": "Plantae",
        "phylum": "Chlorophyta",
        "class_": "Trebouxiophyceae",
        "order_": "Chlorellales",
        "family": "Chlorellaceae",
        "habitat": "Freshwater, ubiquitous in ponds and lakes",
        "biochemical": "High protein content; used in biofuel and nutrition",
        "gbif_id": "5279758",
        "ncbi_id": "3077",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Chlorella.png/220px-Chlorella.png",
        "toxicity": "Non-toxic",
        "bloom_risk": "Low",
        "reference_url": "https://www.algaebase.org/search/species/detail/?species_id=39143",
    },
    {
        "name": "Anabaena",
        "scientific_name": "Anabaena flos-aquae",
        "kingdom": "Bacteria",
        "phylum": "Cyanobacteria",
        "class_": "Cyanophyceae",
        "order_": "Nostocales",
        "family": "Aphanizomenonaceae",
        "habitat": "Freshwater; nitrogen-fixing; common in rice paddies",
        "biochemical": "Nitrogen fixation; produces anatoxin-a and microcystins",
        "gbif_id": "2658867",
        "ncbi_id": "35823",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Anabaena_sperica.jpeg/220px-Anabaena_sperica.jpeg",
        "toxicity": "Potentially toxic (anatoxin-a)",
        "bloom_risk": "High",
        "reference_url": "https://www.algaebase.org/search/species/detail/?species_id=8145",
    },
    {
        "name": "Euglena",
        "scientific_name": "Euglena gracilis",
        "kingdom": "Protozoa",
        "phylum": "Euglenophyta",
        "class_": "Euglenophyceae",
        "order_": "Euglenales",
        "family": "Euglenaceae",
        "habitat": "Stagnant freshwater, nutrient-rich ponds",
        "biochemical": "Paramylon storage compound; high vitamin B12 and wax esters",
        "gbif_id": "4516580",
        "ncbi_id": "3055",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Euglena_diagram.png/220px-Euglena_diagram.png",
        "toxicity": "Non-toxic",
        "bloom_risk": "Low",
        "reference_url": "https://www.algaebase.org/search/species/detail/?species_id=4411",
    },
    {
        "name": "Spirogyra",
        "scientific_name": "Spirogyra communis",
        "kingdom": "Plantae",
        "phylum": "Chlorophyta",
        "class_": "Zygnematophyceae",
        "order_": "Zygnematales",
        "family": "Zygnemataceae",
        "habitat": "Slow-moving freshwater streams and ditches",
        "biochemical": "Cellulosic cell wall; potential biomass feedstock",
        "gbif_id": "5278801",
        "ncbi_id": "35673",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Spirogyra_varians.jpg/220px-Spirogyra_varians.jpg",
        "toxicity": "Non-toxic",
        "bloom_risk": "Low",
        "reference_url": "https://www.algaebase.org/search/species/detail/?species_id=71",
    },
    {
        "name": "Volvox",
        "scientific_name": "Volvox globator",
        "kingdom": "Plantae",
        "phylum": "Chlorophyta",
        "class_": "Chlorophyceae",
        "order_": "Chlamydomonadales",
        "family": "Volvocaceae",
        "habitat": "Freshwater ponds and lakes; eutrophic conditions",
        "biochemical": "Rich in beta-carotene; multicellular model organism",
        "gbif_id": "5278750",
        "ncbi_id": "3066",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Volvox_aureus.jpg/220px-Volvox_aureus.jpg",
        "toxicity": "Non-toxic",
        "bloom_risk": "Low",
        "reference_url": "https://www.algaebase.org/search/species/detail/?species_id=39",
    },
    {
        "name": "Oscillatoria",
        "scientific_name": "Oscillatoria limosa",
        "kingdom": "Bacteria",
        "phylum": "Cyanobacteria",
        "class_": "Cyanophyceae",
        "order_": "Oscillatoriales",
        "family": "Oscillatoriaceae",
        "habitat": "Stagnant freshwater; indicator of eutrophication",
        "biochemical": "Produces microcystin; used in bioremediation studies",
        "gbif_id": "2659172",
        "ncbi_id": "1151",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Oscillatoria_sp.jpg/220px-Oscillatoria_sp.jpg",
        "toxicity": "Potentially toxic (microcystin)",
        "bloom_risk": "High",
        "reference_url": "https://www.algaebase.org/search/species/detail/?species_id=7958",
    },
    {
        "name": "Chlamydomonas",
        "scientific_name": "Chlamydomonas reinhardtii",
        "kingdom": "Plantae",
        "phylum": "Chlorophyta",
        "class_": "Chlorophyceae",
        "order_": "Chlamydomonadales",
        "family": "Chlamydomonadaceae",
        "habitat": "Freshwater ponds, soil, and snow",
        "biochemical": "Model for photosynthesis; hydrogen gas production",
        "gbif_id": "5278620",
        "ncbi_id": "3055",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Chlamydomonas_TEM_17.jpg/220px-Chlamydomonas_TEM_17.jpg",
        "toxicity": "Non-toxic",
        "bloom_risk": "Low",
        "reference_url": "https://www.algaebase.org/search/species/detail/?species_id=82",
    },
    {
        "name": "Diatom_Navicula",
        "scientific_name": "Navicula cryptocephala",
        "kingdom": "Chromista",
        "phylum": "Bacillariophyta",
        "class_": "Bacillariophyceae",
        "order_": "Naviculales",
        "family": "Naviculaceae",
        "habitat": "Freshwater and marine; benthic and planktonic",
        "biochemical": "Silica frustule; high EPA omega-3 fatty acids",
        "gbif_id": "2594990",
        "ncbi_id": "35817",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Navicula_wiki.jpg/220px-Navicula_wiki.jpg",
        "toxicity": "Non-toxic",
        "bloom_risk": "Low",
        "reference_url": "https://www.algaebase.org/search/species/detail/?species_id=45",
    },
    {
        "name": "Microcystis",
        "scientific_name": "Microcystis aeruginosa",
        "kingdom": "Bacteria",
        "phylum": "Cyanobacteria",
        "class_": "Cyanophyceae",
        "order_": "Chroococcales",
        "family": "Microcystaceae",
        "habitat": "Warm eutrophic lakes; bloom-forming in summer",
        "biochemical": "Produces microcystin-LR; highly toxic cyanotoxin",
        "gbif_id": "2658904",
        "ncbi_id": "1126",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Microcystis.jpg/220px-Microcystis.jpg",
        "toxicity": "Highly toxic (microcystin-LR)",
        "bloom_risk": "Very High",
        "reference_url": "https://www.algaebase.org/search/species/detail/?species_id=7970",
    },
    {
        "name": "Pediastrum",
        "scientific_name": "Pediastrum duplex",
        "kingdom": "Plantae",
        "phylum": "Chlorophyta",
        "class_": "Chlorophyceae",
        "order_": "Sphaeropleales",
        "family": "Hydrodictyaceae",
        "habitat": "Planktonic in freshwater lakes and ponds",
        "biochemical": "Bioindicator of water quality; cellulosic biomass",
        "gbif_id": "5279234",
        "ncbi_id": "3055",
        "image_url": "",
        "toxicity": "Non-toxic",
        "bloom_risk": "Low",
        "reference_url": "https://www.algaebase.org/search/species/detail/?species_id=399",
    },
    {
        "name": "Nostoc",
        "scientific_name": "Nostoc commune",
        "kingdom": "Bacteria",
        "phylum": "Cyanobacteria",
        "class_": "Cyanophyceae",
        "order_": "Nostocales",
        "family": "Nostocaceae",
        "habitat": "Freshwater, soil; symbiotic with plants and fungi",
        "biochemical": "Nitrogen fixation; produces nostocyclopeptides and scytonemin",
        "gbif_id": "2659064",
        "ncbi_id": "1177",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/da/Nostoc_commune.jpg/220px-Nostoc_commune.jpg",
        "toxicity": "Mildly toxic (rare)",
        "bloom_risk": "Low",
        "reference_url": "https://www.algaebase.org/search/species/detail/?species_id=8161",
    },
    {
        "name": "Zygnema",
        "scientific_name": "Zygnema circumcarinatum",
        "kingdom": "Plantae",
        "phylum": "Streptophyta",
        "class_": "Zygnematophyceae",
        "order_": "Zygnematales",
        "family": "Zygnemataceae",
        "habitat": "Clean freshwater streams; desiccation-tolerant",
        "biochemical": "Extremophyte; model for land plant evolution",
        "gbif_id": "5278830",
        "ncbi_id": "35674",
        "image_url": "",
        "toxicity": "Non-toxic",
        "bloom_risk": "Low",
        "reference_url": "https://www.algaebase.org/search/species/detail/?species_id=110",
    },
]


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS species_cache (
            name            TEXT PRIMARY KEY,
            scientific_name TEXT,
            kingdom         TEXT,
            phylum          TEXT,
            class_          TEXT,
            order_          TEXT,
            family          TEXT,
            habitat         TEXT,
            biochemical     TEXT,
            gbif_id         TEXT,
            ncbi_id         TEXT,
            image_url       TEXT,
            toxicity        TEXT,
            bloom_risk      TEXT,
            reference_url   TEXT,
            fetched_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS identification_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT,
            predicted_genus TEXT,
            confidence      REAL,
            certainty       TEXT,
            morph_input     TEXT,
            image_used      INTEGER DEFAULT 0,
            timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT,
            predicted_genus TEXT,
            actual_genus    TEXT,
            is_correct      INTEGER,
            notes           TEXT,
            timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    return conn


def seed_database(conn: sqlite3.Connection):
    cur = conn.cursor()
    for row in SEED_DATA:
        cur.execute("""
            INSERT OR REPLACE INTO species_cache
            (name, scientific_name, kingdom, phylum, class_, order_, family,
             habitat, biochemical, gbif_id, ncbi_id, image_url,
             toxicity, bloom_risk, reference_url)
            VALUES (
                :name, :scientific_name, :kingdom, :phylum, :class_, :order_, :family,
                :habitat, :biochemical, :gbif_id, :ncbi_id, :image_url,
                :toxicity, :bloom_risk, :reference_url
            )
        """, row)
    conn.commit()
    print(f"  Seeded {len(SEED_DATA)} species records.")


if __name__ == "__main__":
    print("Initialising AlgoID database...")
    conn = init_db()
    seed_database(conn)
    conn.close()
    print(f"Database ready at {DB_PATH}")
