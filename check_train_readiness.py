"""Pre-train readiness check for PhoBERT fine-tuning.

Muc tieu:
- Kiem tra phan bo nhan tren toan bo du lieu va tap manual.
- Canh bao neu negative manual chua tang so voi baseline.
- Kiem tra che do STRICT_MANUAL_ONLY trong notebook.
- Mo phong stratified split train/val/test de xem support tung lop.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from sklearn.model_selection import train_test_split

DATA_FILE = Path("data/tong_hop_comment.json")
NOTEBOOK_FILE = Path("phobert_finetune.ipynb")
BASELINE_MANUAL_NEGATIVE = 128
SEED = 42

VALID_LABELS = ("positive", "neutral", "negative")


def normalize_sentiment(value: object) -> str:
    sent = str(value or "").strip().lower()
    return sent if sent else "empty"


def load_all_comments(data: dict) -> list[dict]:
    comments: list[dict] = []
    for video in data.get("videos", []):
        comments.extend(video.get("comments", []))
    return comments


def detect_strict_manual_only(nb_path: Path) -> str:
    if not nb_path.exists():
        return "unknown (notebook not found)"

    try:
        nb = json.loads(nb_path.read_text(encoding="utf-8"))
    except Exception:
        return "unknown (cannot parse notebook)"

    found_true = False
    found_false = False

    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        if "STRICT_MANUAL_ONLY" not in source:
            continue
        if "STRICT_MANUAL_ONLY = True" in source:
            found_true = True
        if "STRICT_MANUAL_ONLY = False" in source:
            found_false = True

    if found_true and not found_false:
        return "True"
    if found_false and not found_true:
        return "False"
    if found_true and found_false:
        return "mixed (both True/False found)"
    return "unknown (assignment not found)"


def format_dist(counter: Counter) -> str:
    ordered = [f"{k}={counter.get(k, 0)}" for k in VALID_LABELS]
    extras = [f"{k}={v}" for k, v in counter.items() if k not in VALID_LABELS]
    return ", ".join(ordered + extras)


def main() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing data file: {DATA_FILE}")

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    all_comments = load_all_comments(data)

    manual_comments = [
        c
        for c in all_comments
        if str(c.get("method", "")).strip().lower() == "manual"
    ]

    all_dist = Counter(normalize_sentiment(c.get("sentiment")) for c in all_comments)
    manual_dist = Counter(normalize_sentiment(c.get("sentiment")) for c in manual_comments)

    print("=" * 72)
    print("PRE-TRAIN READINESS CHECK")
    print("=" * 72)
    print(f"Data file               : {DATA_FILE}")
    print(f"Total comments          : {len(all_comments)}")
    print(f"Manual comments         : {len(manual_comments)}")
    print(f"All label dist          : {format_dist(all_dist)}")
    print(f"Manual label dist       : {format_dist(manual_dist)}")

    manual_neg = manual_dist.get("negative", 0)
    delta_neg = manual_neg - BASELINE_MANUAL_NEGATIVE
    sign = "+" if delta_neg >= 0 else ""
    print(
        f"Manual negative delta   : {manual_neg} (baseline {BASELINE_MANUAL_NEGATIVE}, {sign}{delta_neg})"
    )

    strict_mode = detect_strict_manual_only(NOTEBOOK_FILE)
    print(f"STRICT_MANUAL_ONLY      : {strict_mode}")

    # Trainable set = manual + valid labels only
    trainable = [
        c
        for c in manual_comments
        if normalize_sentiment(c.get("sentiment")) in VALID_LABELS
    ]
    print(f"Trainable manual rows   : {len(trainable)}")

    if len(trainable) < 30:
        print("\n[BLOCKER] Qua it du lieu trainable.")
        return

    # Stratified split preview
    texts = [str(c.get("text", "")) for c in trainable]
    y = [normalize_sentiment(c.get("sentiment")) for c in trainable]

    x_train, x_temp, y_train, y_temp = train_test_split(
        texts,
        y,
        test_size=0.30,
        random_state=SEED,
        stratify=y,
    )
    x_val, x_test, y_val, y_test = train_test_split(
        x_temp,
        y_temp,
        test_size=0.50,
        random_state=SEED,
        stratify=y_temp,
    )

    print("\nSplit preview (stratified):")
    print(f"  Train={len(x_train)}, Val={len(x_val)}, Test={len(x_test)}")
    print(f"  Train dist: {format_dist(Counter(y_train))}")
    print(f"  Val dist  : {format_dist(Counter(y_val))}")
    print(f"  Test dist : {format_dist(Counter(y_test))}")

    # Heuristic alerts
    alerts: list[str] = []
    if manual_neg <= BASELINE_MANUAL_NEGATIVE:
        alerts.append("Negative manual chua tang so voi baseline -> kho ky vong F1 macro tang ro.")
    if strict_mode.startswith("True") and all_dist.get("negative", 0) > manual_neg:
        alerts.append("Co negative moi o tong data nhung khong phai manual -> train manual-only se bo qua.")
    if Counter(y_val).get("negative", 0) < 15:
        alerts.append("So mau negative o val qua it -> metric dao dong manh.")
    if Counter(y_test).get("negative", 0) < 15:
        alerts.append("So mau negative o test qua it -> ket qua danh gia chua on dinh.")

    print("\nAssessment:")
    if not alerts:
        print("  READY: Co the train va so sanh ket qua hop ly.")
    else:
        for i, msg in enumerate(alerts, start=1):
            print(f"  {i}. {msg}")


if __name__ == "__main__":
    main()
