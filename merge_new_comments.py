"""Merge TikTok profile/comment exports into dashboard and training sources.

Targets updated by this script:
1. data/tong_hop_comment.json
2. data/merged/tiktok_travinhuniversity_merged.json

Rules:
- Only keep comments from @travinhuniversity.
- Deduplicate primarily by cid, then by (video_id, text, author, created_at).
- New comments are added as method='unlabeled' for dashboard review.
- Recompute comment/video sentiment summaries to keep dashboard stats consistent.
- Enrich/create merged videos from the latest profile export so new videos also appear in dashboard pages.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
COMMENTS_FILE = BASE_DIR / "dataset_tiktok-comments-scraper_2026-03-13_07-24-49-844.json"
PROFILE_FILE = BASE_DIR / "dataset_tiktok-profile-scraper_2026-03-13_07-29-58-885.json"
MASTER_FILE = BASE_DIR / "data" / "tong_hop_comment.json"
MERGED_FILE = BASE_DIR / "data" / "merged" / "tiktok_travinhuniversity_merged.json"

CHANNEL_NAME = "travinhuniversity"
VALID_SENTIMENTS = ("positive", "neutral", "negative")


def load_json(path: Path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def norm_text(value: object) -> str:
    return str(value or "").strip()


def norm_sentiment(value: object) -> str:
    sent = str(value or "").strip().lower()
    return sent if sent in VALID_SENTIMENTS else ""


def safe_int(value: object) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def parse_video_id(url: object) -> str:
    url = str(url or "").strip().rstrip("/")
    if "/video/" not in url:
        return ""
    return url.split("/")[-1]


def is_target_comment(row: dict) -> bool:
    url = str(row.get("videoWebUrl", ""))
    return f"@{CHANNEL_NAME}/video/" in url


def build_comment_dedupe_state(master_data: dict):
    cid_set: set[str] = set()
    composite_set: set[tuple[str, str, str, str]] = set()

    for video in master_data.get("videos", []):
        video_id = str(video.get("video_id", ""))
        for comment in video.get("comments", []):
            cid = str(comment.get("cid", "")).strip()
            if cid:
                cid_set.add(cid)
            composite_set.add(
                (
                    video_id,
                    norm_text(comment.get("text", "")).lower(),
                    str(comment.get("author", "")).strip().lower(),
                    str(comment.get("created_at", "")).strip(),
                )
            )
    return cid_set, composite_set


def make_comment(row: dict) -> dict:
    url = str(row.get("videoWebUrl", "")).strip()
    return {
        "text": norm_text(row.get("text", "")),
        "author": str(row.get("uniqueId", "")).strip(),
        "likes": safe_int(row.get("diggCount", 0)),
        "video_id": parse_video_id(url),
        "video_url": url,
        "created_at": str(row.get("createTimeISO", "")).strip(),
        "sentiment": "",
        "confidence": 0.0,
        "language": "vi",
        "method": "unlabeled",
        "cid": str(row.get("cid", "")).strip(),
    }


def compute_sentiment_summary(comments: list[dict]) -> tuple[dict, dict]:
    counts = {label: 0 for label in VALID_SENTIMENTS}
    for comment in comments:
        sent = norm_sentiment(comment.get("sentiment", ""))
        if sent:
            counts[sent] += 1
    labeled_total = sum(counts.values())
    percentages = {
        label: round((counts[label] / labeled_total) * 100, 6) if labeled_total else 0.0
        for label in VALID_SENTIMENTS
    }
    return counts, percentages


def refresh_master_stats(master_data: dict) -> None:
    global_counts = Counter()
    total_comments = 0
    total_likes = 0

    for video in master_data.get("videos", []):
        comments = video.get("comments", [])
        video["comments_count"] = len(comments)
        video["total_likes"] = sum(safe_int(comment.get("likes", 0)) for comment in comments)
        video["avg_likes_per_comment"] = round(video["total_likes"] / len(comments), 2) if comments else 0
        summary, percentages = compute_sentiment_summary(comments)
        video["sentiment_summary"] = summary
        video["sentiment_percentages"] = percentages

        total_comments += len(comments)
        total_likes += video["total_likes"]
        global_counts.update(summary)

    labeled_total = sum(global_counts.values())
    master_data["total_videos"] = len(master_data.get("videos", []))
    master_data["total_comments"] = total_comments
    master_data["total_likes"] = total_likes
    master_data["analyzed_at"] = datetime.now().isoformat(timespec="seconds")
    master_data["global_sentiment_summary"] = {
        label: {
            "count": global_counts.get(label, 0),
            "percentage": (global_counts.get(label, 0) / labeled_total * 100) if labeled_total else 0.0,
        }
        for label in VALID_SENTIMENTS
    }


def extract_hashtags(text: object) -> list[str]:
    hashtags: list[str] = []
    for token in str(text or "").split():
        if token.startswith("#"):
            hashtags.append(token)
    return hashtags


def compute_metrics(stats: dict) -> dict:
    play_count = safe_int(stats.get("play_count", 0))

    def rate(value: int) -> float:
        return round((value / play_count) * 100, 2) if play_count else 0.0

    like_count = safe_int(stats.get("like_count", 0))
    comment_count = safe_int(stats.get("comment_count", 0))
    share_count = safe_int(stats.get("share_count", 0))
    collect_count = safe_int(stats.get("collect_count", 0))

    return {
        "engagement_rate": rate(like_count + comment_count + share_count + collect_count),
        "like_rate": rate(like_count),
        "comment_rate": rate(comment_count),
        "share_rate": rate(share_count),
        "collect_rate": rate(collect_count),
    }


def build_video_from_profile(profile_row: dict | None, fallback_video: dict | None = None) -> dict:
    fallback_video = fallback_video or {}
    video_id = parse_video_id((profile_row or {}).get("webVideoUrl") or fallback_video.get("video_url"))
    video_url = str((profile_row or {}).get("webVideoUrl") or fallback_video.get("video_url") or "").strip()
    stats = {
        "play_count": safe_int((profile_row or {}).get("playCount", fallback_video.get("stats", {}).get("play_count", 0))),
        "like_count": safe_int((profile_row or {}).get("diggCount", fallback_video.get("stats", {}).get("like_count", 0))),
        "comment_count": safe_int((profile_row or {}).get("commentCount", fallback_video.get("stats", {}).get("comment_count", 0))),
        "share_count": safe_int((profile_row or {}).get("shareCount", fallback_video.get("stats", {}).get("share_count", 0))),
        "collect_count": safe_int(fallback_video.get("stats", {}).get("collect_count", 0)),
    }

    description = str((profile_row or {}).get("text") or fallback_video.get("description") or "").strip()
    first_line = next((line.strip() for line in description.splitlines() if line.strip()), "")

    return {
        "id": video_id,
        "author_name": str((profile_row or {}).get("authorMeta.name") or fallback_video.get("author_name") or CHANNEL_NAME),
        "author_id": str(fallback_video.get("author_id", "")),
        "description": description,
        "duration": safe_int((profile_row or {}).get("videoMeta.duration", fallback_video.get("duration", 0))),
        "title": first_line or str(fallback_video.get("title") or ""),
        "video_url": video_url,
        "cover_url": str(fallback_video.get("cover_url", "")),
        "create_time": str((profile_row or {}).get("createTimeISO") or fallback_video.get("create_time") or ""),
        "hashtags": extract_hashtags(description) or fallback_video.get("hashtags", []),
        "is_ad": bool(fallback_video.get("is_ad", False)),
        "stats": stats,
        "metrics": compute_metrics(stats),
        "music": {
            "title": str((profile_row or {}).get("musicMeta.musicName") or fallback_video.get("music", {}).get("title") or ""),
            "author": str((profile_row or {}).get("musicMeta.musicAuthor") or fallback_video.get("music", {}).get("author") or ""),
            "id": str(fallback_video.get("music", {}).get("id", "")),
            "original": bool((profile_row or {}).get("musicMeta.musicOriginal", fallback_video.get("music", {}).get("original", False))),
        },
        "metadata": deepcopy(fallback_video.get("metadata", {"resolution": "", "ratio": "", "size_mb": 0})),
        "comments": [],
        "has_sentiment": False,
    }


def refresh_merged_data(merged_data: dict, master_data: dict, profile_rows: list[dict]) -> dict:
    master_video_map = {str(video.get("video_id", "")): video for video in master_data.get("videos", [])}
    merged_video_map = {str(video.get("id", "")): video for video in merged_data.get("videos", [])}
    profile_map = {}

    for row in profile_rows:
        video_id = parse_video_id(row.get("webVideoUrl"))
        if video_id:
            profile_map[video_id] = row

    ordered_ids: list[str] = []
    seen_ids: set[str] = set()
    for source_ids in (
        [str(video.get("id", "")) for video in merged_data.get("videos", [])],
        list(profile_map.keys()),
        list(master_video_map.keys()),
    ):
        for video_id in source_ids:
            if video_id and video_id not in seen_ids:
                ordered_ids.append(video_id)
                seen_ids.add(video_id)

    rebuilt_videos = []
    flattened_comments = []

    for video_id in ordered_ids:
        existing_video = merged_video_map.get(video_id)
        profile_row = profile_map.get(video_id)
        master_video = master_video_map.get(video_id)
        rebuilt_video = build_video_from_profile(profile_row, existing_video)

        if master_video is not None:
            rebuilt_video["comments"] = deepcopy(master_video.get("comments", []))
            rebuilt_video["has_sentiment"] = bool(rebuilt_video["comments"])
            rebuilt_video["stats"]["comment_count"] = max(
                safe_int(rebuilt_video["stats"].get("comment_count", 0)),
                len(rebuilt_video["comments"]),
            )
            rebuilt_video["metrics"] = compute_metrics(rebuilt_video["stats"])
            flattened_comments.extend(deepcopy(rebuilt_video["comments"]))
        elif existing_video is not None:
            rebuilt_video["comments"] = deepcopy(existing_video.get("comments", []))
            rebuilt_video["has_sentiment"] = bool(rebuilt_video["comments"])
            flattened_comments.extend(deepcopy(rebuilt_video["comments"]))

        rebuilt_videos.append(rebuilt_video)

    for comment in flattened_comments:
        if not comment.get("video_id"):
            comment["video_id"] = parse_video_id(comment.get("video_url"))

    merged_data["videos"] = rebuilt_videos
    merged_data["comments"] = flattened_comments
    metadata = merged_data.setdefault("metadata", {})
    metadata.update(
        {
            "platform": "tiktok",
            "identifier": CHANNEL_NAME,
            "collected_at": datetime.now().isoformat(timespec="seconds"),
            "merger_version": "2.0.0",
            "source_video_stats": PROFILE_FILE.name,
            "source_comments": MASTER_FILE.name,
            "accuracy": master_data.get("accuracy", metadata.get("accuracy", "~92% for Vietnamese")),
            "model": master_data.get("model", metadata.get("model", "PhoBERT")),
            "total_videos": len(rebuilt_videos),
            "videos_with_comments": sum(1 for video in rebuilt_videos if video.get("comments")),
            "total_comments": len(flattened_comments),
        }
    )
    return merged_data


def main() -> None:
    master_data = load_json(MASTER_FILE)
    merged_data = load_json(MERGED_FILE)
    new_comments_raw = load_json(COMMENTS_FILE)
    profile_rows = load_json(PROFILE_FILE)

    cid_set, composite_set = build_comment_dedupe_state(master_data)
    video_map = {str(video.get("video_id", "")): video for video in master_data.get("videos", [])}

    counts = Counter()
    valid_new_comments: list[dict] = []

    for row in new_comments_raw:
        url = str(row.get("videoWebUrl", "")).strip()
        if not is_target_comment(row):
            counts["wrong_channel"] += 1
            continue

        comment = make_comment(row)
        video_id = comment["video_id"]
        text = norm_text(comment["text"])
        if not video_id or len(text) < 2:
            counts["empty_or_invalid"] += 1
            continue

        cid = str(comment.get("cid", "")).strip()
        composite_key = (
            video_id,
            text.lower(),
            str(comment.get("author", "")).strip().lower(),
            str(comment.get("created_at", "")).strip(),
        )

        if cid and cid in cid_set:
            counts["duplicate"] += 1
            continue
        if composite_key in composite_set:
            counts["duplicate"] += 1
            continue

        if cid:
            cid_set.add(cid)
        composite_set.add(composite_key)
        valid_new_comments.append(comment)

    new_by_video: dict[str, list[dict]] = defaultdict(list)
    for comment in valid_new_comments:
        new_by_video[comment["video_id"]].append(comment)

    videos_updated = 0
    videos_created = 0
    for video_id, comments in new_by_video.items():
        if video_id in video_map:
            video_map[video_id].setdefault("comments", []).extend(comments)
            videos_updated += 1
        else:
            master_video = {
                "video_id": video_id,
                "video_url": comments[0].get("video_url", ""),
                "comments_count": 0,
                "total_likes": 0,
                "avg_likes_per_comment": 0,
                "comments": comments,
                "sentiment_summary": {label: 0 for label in VALID_SENTIMENTS},
                "sentiment_percentages": {label: 0.0 for label in VALID_SENTIMENTS},
            }
            master_data.setdefault("videos", []).append(master_video)
            video_map[video_id] = master_video
            videos_created += 1

    refresh_master_stats(master_data)
    refreshed_merged = refresh_merged_data(merged_data, master_data, profile_rows)

    save_json(MASTER_FILE, master_data)
    save_json(MERGED_FILE, refreshed_merged)

    manual_count = sum(
        1
        for video in master_data.get("videos", [])
        for comment in video.get("comments", [])
        if str(comment.get("method", "")).strip().lower() == "manual"
    )
    unlabeled_count = sum(
        1
        for video in master_data.get("videos", [])
        for comment in video.get("comments", [])
        if str(comment.get("method", "")).strip().lower() == "unlabeled"
    )

    print("=" * 72)
    print("MERGE COMPLETED")
    print("=" * 72)
    print(f"Filtered wrong channel : {counts['wrong_channel']}")
    print(f"Filtered duplicates    : {counts['duplicate']}")
    print(f"Filtered empty/invalid : {counts['empty_or_invalid']}")
    print(f"New comments added     : {len(valid_new_comments)}")
    print(f"Existing videos updated: {videos_updated}")
    print(f"New master videos      : {videos_created}")
    print(f"Master total videos    : {master_data['total_videos']}")
    print(f"Master total comments  : {master_data['total_comments']}")
    print(f"Merged total videos    : {refreshed_merged['metadata']['total_videos']}")
    print(f"Merged total comments  : {refreshed_merged['metadata']['total_comments']}")
    print(f"Manual comments        : {manual_count}")
    print(f"Unlabeled comments     : {unlabeled_count}")
    print(f"Saved master           : {MASTER_FILE}")
    print(f"Saved merged           : {MERGED_FILE}")


if __name__ == "__main__":
    main()
