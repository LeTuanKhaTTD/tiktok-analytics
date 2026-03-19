"""Prepare clean training datasets for PhoBERT retraining.

Creates two files from the merged TikTok data:
1) Manual-only (ground truth)
2) Manual + PhoBERT pseudo labels

This helps run reproducible retraining with explicit dataset sizes.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from sklearn.model_selection import train_test_split


VALID_SENTIMENTS = {"positive", "neutral", "negative"}


def load_comments(source_path: Path) -> tuple[list[dict], str]:
    with source_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    comments: list[dict] = []
    shape = "unknown"

    if isinstance(raw, dict) and isinstance(raw.get("comments"), list):
        comments = raw["comments"]
        shape = "flat.comments"
    elif isinstance(raw, dict) and isinstance(raw.get("videos"), list):
        for video in raw["videos"]:
            comments.extend(video.get("comments", []))
        shape = "nested.videos.comments"
    elif isinstance(raw, list):
        comments = raw
        shape = "list"

    return comments, shape


def clean_and_filter(comments: list[dict], allowed_methods: set[str]) -> tuple[list[dict], Counter]:
    cleaned: list[dict] = []
    skipped = Counter()

    for c in comments:
        sent = str(c.get("sentiment", "")).strip().lower()
        method = str(c.get("method", "")).strip().lower()
        text = str(c.get("text", "")).strip()

        if sent not in VALID_SENTIMENTS:
            skipped["invalid_sentiment"] += 1
            continue
        if method not in allowed_methods:
            skipped[f"method:{method or '<empty>'}"] += 1
            continue
        if not text:
            skipped["empty_text"] += 1
            continue

        item = dict(c)
        item["sentiment"] = sent
        item["method"] = method
        cleaned.append(item)

    return cleaned, skipped


def clean_all_labeled(comments: list[dict]) -> tuple[list[dict], Counter]:
    """Keep all rows that have valid sentiment; normalize empty method."""
    cleaned: list[dict] = []
    skipped = Counter()

    for c in comments:
        sent = str(c.get("sentiment", "")).strip().lower()
        method = str(c.get("method", "")).strip().lower()
        text = str(c.get("text", "")).strip()

        if sent not in VALID_SENTIMENTS:
            skipped["invalid_sentiment"] += 1
            continue
        if not text:
            skipped["empty_text"] += 1
            continue

        item = dict(c)
        item["sentiment"] = sent
        # Ensure notebook method filtering keeps fully-labeled rows.
        item["method"] = method or "manual"
        cleaned.append(item)

    return cleaned, skipped


def expected_split_sizes(comments: list[dict]) -> dict[str, int]:
    labels = [str(c.get("sentiment", "")).strip().lower() for c in comments]
    x = list(range(len(labels)))

    x_train, x_temp, y_train, y_temp = train_test_split(
        x,
        labels,
        test_size=0.30,
        random_state=42,
        stratify=labels,
    )
    x_val, x_test = train_test_split(
        x_temp,
        test_size=0.50,
        random_state=42,
        stratify=y_temp,
    )
    return {"train": len(x_train), "val": len(x_val), "test": len(x_test)}


def save_dataset(out_path: Path, comments: list[dict], source_path: Path, mode: str, skipped: Counter) -> None:
    method_counts = Counter(str(c.get("method", "")).strip().lower() for c in comments)
    sentiment_counts = Counter(str(c.get("sentiment", "")).strip().lower() for c in comments)
    split = expected_split_sizes(comments)

    payload = {
        "metadata": {
            "source_file": str(source_path).replace("\\", "/"),
            "mode": mode,
            "total_comments": len(comments),
            "method_counts": dict(method_counts),
            "sentiment_counts": dict(sentiment_counts),
            "expected_split_70_15_15": split,
            "skipped": dict(skipped),
        },
        "comments": comments,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare datasets for PhoBERT retraining")
    parser.add_argument(
        "--source",
        default="data/merged/tiktok_travinhuniversity_merged.json",
        help="Input JSON source (merged/comments/list)",
    )
    parser.add_argument(
        "--out-dir",
        default="data/export",
        help="Output directory for prepared datasets",
    )
    args = parser.parse_args()

    source_path = Path(args.source)
    out_dir = Path(args.out_dir)

    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    comments, shape = load_comments(source_path)
    print(f"Source: {source_path}")
    print(f"Shape: {shape}")
    print(f"Raw comments: {len(comments)}")

    manual_comments, skipped_manual = clean_and_filter(comments, {"manual"})
    full_comments, skipped_full = clean_and_filter(comments, {"manual", "phobert"})
    all_labeled_comments, skipped_all = clean_all_labeled(comments)

    out_manual = out_dir / "retrain_manual_only_2004.json"
    out_full = out_dir / "retrain_manual_phobert_2782.json"
    out_all = out_dir / "retrain_all_labeled_2865.json"

    save_dataset(out_manual, manual_comments, source_path, "manual_only", skipped_manual)
    save_dataset(out_full, full_comments, source_path, "manual_plus_phobert", skipped_full)
    save_dataset(out_all, all_labeled_comments, source_path, "all_labeled_valid_sentiment", skipped_all)

    print("\nPrepared datasets:")
    print(f"- {out_manual} | n={len(manual_comments)} | split={expected_split_sizes(manual_comments)}")
    print(f"- {out_full}   | n={len(full_comments)} | split={expected_split_sizes(full_comments)}")
    print(f"- {out_all}    | n={len(all_labeled_comments)} | split={expected_split_sizes(all_labeled_comments)}")


if __name__ == "__main__":
    main()
