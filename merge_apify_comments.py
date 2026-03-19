"""Ghép dữ liệu Apify Video Stats với Comment Sentiment

Module này ghép 2 nguồn dữ liệu:
1. Video stats từ Apify (100 video với đầy đủ plays, likes, shares, saves)
2. Comment sentiment từ tong_hop_comment.json (đã được PhoBERT gán nhãn)

Kết quả: File merged chứa tất cả thông tin video + bình luận + sentiment
Lưu tại: data/merged/tiktok_travinhuniversity_merged.json
"""
import json
from datetime import datetime
from pathlib import Path

def merge_data():
    """Ghép video stats từ Apify với comment sentiment từ PhoBERT
    
    Quy trình:
    1. Đọc dữ liệu video từ file validated (Apify)
    2. Đọc dữ liệu bình luận từ file tong_hop_comment.json
    3. Ghép bình luận vào video tương ứng theo video_id
    4. Lưu kết quả ghép vào data/merged/
    """
    
    print("=" * 70)
    print("🔀 MERGING DATA SOURCES")
    print("=" * 70)
    print()
    
    # Đọc thống kê video từ Apify (100 video với plays, likes, shares, saves)
    print("\U0001f4e5 Loading Apify video stats...")
    with open("data/validated/tiktok_travinhuniversity_20260306_151259_validated.json", 'r', encoding='utf-8') as f:
        apify_data = json.load(f)
    
    # Đọc dữ liệu sentiment bình luận (đã được PhoBERT phân tích)
    print("\U0001f4e5 Loading comment sentiment data...")
    with open("data/tong_hop_comment.json", 'r', encoding='utf-8') as f:
        comment_data = json.load(f)
    
    # Tạo mapping: video_id -> danh sách comments
    print("🔗 Mapping comments to videos...")
    video_comments = {}
    for video in comment_data.get('videos', []):
        video_id = video.get('video_id')
        video_comments[video_id] = video.get('comments', [])
    
    # Ghép bình luận vào từng video theo video_id
    merged_videos = []
    matched_videos = 0    # Số video có bình luận khớp
    total_comments_merged = 0  # Tổng số bình luận đã ghép
    
    for video in apify_data.get('videos', []):
        video_id = video.get('id')
        
        # Thêm bình luận vào video nếu có khớp video_id
        if video_id in video_comments:
            comments = video_comments[video_id]
            video['comments'] = comments
            video['has_sentiment'] = True
            matched_videos += 1
            total_comments_merged += len(comments)
        else:
            video['comments'] = []
            video['has_sentiment'] = False
        
        merged_videos.append(video)
    
    # Tạo dataset đã ghép kèm metadata đầy đủ
    merged_data = {
        "metadata": {
            "platform": "tiktok",
            "identifier": "travinhuniversity",
            "collected_at": datetime.now().isoformat(),
            "merger_version": "1.0.0",
            "source_video_stats": "Apify Profile Scraper",
            "source_comments": "tong_hop_comment.json (PhoBERT sentiment)",
            "accuracy": comment_data.get('accuracy', '~92% for Vietnamese'),
            "model": comment_data.get('model', 'PhoBERT'),
            "total_videos": len(merged_videos),
            "videos_with_comments": matched_videos,
            "total_comments": total_comments_merged
        },
        "user": apify_data.get('user', {}),
        "videos": merged_videos,
        "comments": []  # Flatten later if needed
    }
    
    # Làm phẳng: gộp tất cả comments vào một danh sách chung
    all_comments = []
    for video in merged_videos:
        for comment in video.get('comments', []):
            comment['video_id'] = video.get('id')
            all_comments.append(comment)
    
    merged_data['comments'] = all_comments
    
    # Lưu dữ liệu đã ghép
    output_path = Path("data/merged/tiktok_travinhuniversity_merged.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    print()
    print("✅ MERGE COMPLETED!")
    print(f"   Videos merged: {len(merged_videos)}")
    print(f"   Videos with comments: {matched_videos}")
    print(f"   Total comments: {total_comments_merged}")
    print(f"   Saved to: {output_path}")
    print()
    
    return merged_data

if __name__ == "__main__":
    merged_data = merge_data()
