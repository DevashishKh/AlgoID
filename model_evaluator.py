"""
modules/model_evaluator.py
Evaluate AlgoID prediction accuracy against a labeled test set.

Usage (morphology):
    python modules/model_evaluator.py --mode morphology --test data/test_morphology.csv

Usage (image CNN):
    python modules/model_evaluator.py --mode image --test data/algae_dataset_test/

Outputs: confusion matrix, per-class precision/recall/F1, overall accuracy.
"""

import argparse
import csv
import json
from pathlib import Path
from collections import defaultdict


# ── Morphology evaluation ─────────────────────────────────────────────────────

def evaluate_morphology(test_csv: str):
    """
    Test CSV must have columns:
        sample_id, shape, pigmentation, motility, special_structures, true_genus
    """
    from modules.morphology_engine import identify_from_morphology

    path = Path(test_csv)
    if not path.exists():
        print(f"File not found: {test_csv}")
        return

    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    y_true, y_pred = [], []

    for row in rows:
        structs = [s.strip() for s in row.get("special_structures","").split("|") if s.strip()]
        inp = {
            "shape": row["shape"],
            "pigmentation": row["pigmentation"],
            "motility": row.get("motility","false").lower() in ("true","1","yes"),
            "special_structures": structs,
        }
        preds = identify_from_morphology(inp, top_n=1)
        predicted = preds[0]["genus"] if preds else "Unknown"
        y_true.append(row["true_genus"].strip())
        y_pred.append(predicted)

    _print_metrics("Morphology engine", y_true, y_pred)


# ── Image CNN evaluation ──────────────────────────────────────────────────────

def evaluate_images(test_dir: str):
    """
    test_dir must follow ImageFolder layout:
        test_dir/Chlorella/img1.jpg
        test_dir/Euglena/img2.png
        ...
    """
    from PIL import Image
    from modules.image_classifier import predict_from_image

    base = Path(test_dir)
    if not base.exists():
        print(f"Directory not found: {test_dir}")
        return

    y_true, y_pred = [], []

    for class_dir in sorted(base.iterdir()):
        if not class_dir.is_dir():
            continue
        true_label = class_dir.name
        imgs = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png")) + list(class_dir.glob("*.jpeg"))
        print(f"  {true_label}: {len(imgs)} images")
        for img_path in imgs:
            try:
                pil = Image.open(img_path).convert("RGB")
                preds = predict_from_image(pil, top_n=1)
                predicted = preds[0]["species"] if preds else "Unknown"
            except Exception as e:
                print(f"    Skip {img_path.name}: {e}")
                continue
            y_true.append(true_label)
            y_pred.append(predicted)

    _print_metrics("CNN Image classifier", y_true, y_pred)


# ── Shared metrics ────────────────────────────────────────────────────────────

def _print_metrics(title: str, y_true: list, y_pred: list):
    classes = sorted(set(y_true) | set(y_pred))
    n = len(y_true)

    # Confusion matrix as dict
    cm: dict = defaultdict(lambda: defaultdict(int))
    for t, p in zip(y_true, y_pred):
        cm[t][p] += 1

    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    overall_acc = correct / n if n else 0

    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(f"  Samples evaluated : {n}")
    print(f"  Overall accuracy  : {overall_acc*100:.2f}%")
    print(f"\n  {'Class':<22} {'Prec':>6} {'Rec':>6} {'F1':>6} {'Support':>8}")
    print(f"  {'-'*52}")

    macro_p, macro_r, macro_f = [], [], []
    for cls in classes:
        tp = cm[cls][cls]
        fp = sum(cm[other][cls] for other in classes if other != cls)
        fn = sum(cm[cls][other] for other in classes if other != cls)
        prec = tp / (tp + fp) if (tp + fp) else 0
        rec  = tp / (tp + fn) if (tp + fn) else 0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0
        sup  = sum(cm[cls].values())
        macro_p.append(prec); macro_r.append(rec); macro_f.append(f1)
        print(f"  {cls:<22} {prec:>6.3f} {rec:>6.3f} {f1:>6.3f} {sup:>8}")

    print(f"  {'-'*52}")
    mp = sum(macro_p)/len(macro_p) if macro_p else 0
    mr = sum(macro_r)/len(macro_r) if macro_r else 0
    mf = sum(macro_f)/len(macro_f) if macro_f else 0
    print(f"  {'Macro avg':<22} {mp:>6.3f} {mr:>6.3f} {mf:>6.3f}")

    # Confusion matrix print
    print(f"\n  Confusion matrix (rows=true, cols=predicted):")
    header = f"  {'':>18}" + "".join(f"{c[:8]:>9}" for c in classes)
    print(header)
    for t in classes:
        row_str = f"  {t[:18]:<18}" + "".join(
            f"{cm[t].get(p,0):>9}" for p in classes
        )
        print(row_str)

    # Save JSON report
    report = {
        "title": title,
        "n_samples": n,
        "overall_accuracy": round(overall_acc, 4),
        "macro_precision": round(mp, 4),
        "macro_recall": round(mr, 4),
        "macro_f1": round(mf, 4),
    }
    out = Path(f"eval_{title.replace(' ','_').lower()}.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report saved → {out}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AlgoID model evaluator")
    parser.add_argument("--mode", choices=["morphology","image"], required=True)
    parser.add_argument("--test", required=True,
                        help="CSV file (morphology) or directory (image)")
    args = parser.parse_args()

    if args.mode == "morphology":
        evaluate_morphology(args.test)
    else:
        evaluate_images(args.test)
