# AlgoID – Intelligent Algae Identification System

A hybrid AI system for identifying freshwater microalgae using morphological
features and/or microscope images.

## Quick start

```bash
# 1. Clone / unzip the project
cd AlgoID

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialise and seed the database (run once)
python database_setup.py

# 4. Launch the app
streamlit run app.py
```

The app opens at http://localhost:8501

## Train the CNN (optional)

Collect labeled microscopy images into:

```
data/algae_dataset/
  Chlorella/      ← ≥100 images per class
  Euglena/
  Spirogyra/
  ...
```

Then run:

```bash
python -c "from modules.image_classifier import train_model; train_model()"
```

Training without GPU takes ~30 min on CPU. The saved model lands in
`models/algae_cnn/` and is loaded automatically by the app.

## Dataset sources

- Kaggle: search "algae microscopy"
- AlgaeBase image galleries (algaebase.org)
- CSIRO Microalgae Identification Database
- Published microscopy papers (open-access figures)

## Project structure

```
AlgoID/
├── app.py                    ← Streamlit UI (entry point)
├── database_setup.py         ← DB init + seed (run once)
├── requirements.txt
├── data/
│   ├── morphology_rules.json ← 12-genus knowledge base
│   ├── algae_dataset/        ← place training images here
│   └── sqlite_cache.db       ← auto-created on first run
├── modules/
│   ├── morphology_engine.py  ← rule-based scoring
│   ├── image_classifier.py   ← CNN inference + training
│   ├── hybrid_engine.py      ← weighted fusion
│   └── db_connector.py       ← GBIF / NCBI / SQLite
├── models/algae_cnn/         ← saved TF model (after training)
└── utils/
    └── result_formatter.py   ← JSON report builder
```

## Extending the knowledge base

Edit `data/morphology_rules.json` to add new genera:

```json
"NewGenus": {
  "shape": ["unicellular"],
  "pigmentation": ["green"],
  "motility": false,
  "special_structures": [],
  "habitat": "describe habitat",
  "biochemical": "describe biochemistry",
  "division": "Chlorophyta",
  "score_weight": 1.0
}
```

Then add a matching entry in `database_setup.py` `SEED_DATA` list and
re-run `python database_setup.py`.
