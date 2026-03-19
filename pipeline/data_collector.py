"""Data Collector - Thu thập dữ liệu thô (demo/mock)

Module này tạo dữ liệu mẫu giả lập cho mục đích demo.
Trong thực tế, dữ liệu được thu thập từ Apify (xem apify_importer.py).

Dữ liệu mẫu bao gồm:
- Thông tin tài khoản (user profile)
- Danh sách video với thống kê ngẫu nhiên
- Bình luận mẫu bằng tiếng Việt và tiếng Anh
"""
import json
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

class DataCollector:
    """Lớp thu thập dữ liệu TikTok (mock data cho demo)"""
    
    def __init__(self, output_dir: str = "data/raw"):
        """Khởi tạo DataCollector với thư mục lưu dữ liệu thô"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"? DataCollector initialized: {self.output_dir}")
    
    def collect_tiktok(self, username: str, max_videos: int = 30) -> Dict[str, Any]:
        """Tạo dữ liệu mẫu TikTok giả lập cho mục đích demo
        
        Args:
            username: Tên tài khoản TikTok
            max_videos: Số video tối đa cần tạo
            
        Returns:
            Dữ liệu thô gồm thông tin user, videos và comments
        """
        print(f"\n📥 Collecting TikTok data: @{username}")
        
        # Tập hợp hashtag mẫu
        hashtags_pool = ["#fyp", "#viral", "#trending", "#foryou", "#duet", "#comedy", 
                        "#dance", "#music", "#tutorial", "#food", "#travel", "#lifestyle"]
        # Mô tả video mẫu
        descriptions_pool = [
            "Amazing day at the beach! 🌊",
            "Can't believe this happened 😱",
            "Tutorial: How to...",
            "Day in my life vlog 📹",
            "This is so funny 😂",
            "New recipe alert! 🍕",
            "Travel guide to...",
            "Rate my outfit 👗",
            "Behind the scenes",
            "Life hack you need to know"
        ]
        # Nhạc nền mẫu
        music_pool = [
            {"id": "m001", "title": "Original Sound", "author": "Various"},
            {"id": "m002", "title": "Trending Song 2026", "author": "Popular Artist"},
            {"id": "m003", "title": "Viral Beat", "author": "DJ Mix"},
            {"id": "m004", "title": "Chill Vibes", "author": "Lofi Creator"},
        ]
        
        # Tạo cấu trúc dữ liệu thô chuẩn của pipeline
        raw_data = {
            "metadata": {
                "platform": "tiktok",
                "identifier": username,
                "collected_at": datetime.now().isoformat(),
                "collector_version": "2.0.0",
                "api_endpoint": "https://api.tiktok.com/v1/",
                "total_api_calls": max_videos
            },
            "user": {
                "username": username,
                "user_id": f"user_{random.randint(100000, 999999)}",
                "nickname": username.replace("_", " ").title(),
                "avatar_url": f"https://cdn.tiktok.com/avatar/{username}.jpg",
                "signature": "Content creator | Lifestyle | Travel",
                "follower_count": random.randint(5000, 500000),
                "following_count": random.randint(100, 1000),
                "video_count": random.randint(50, 500),
                "likes_count": random.randint(10000, 1000000),
                "verified": random.choice([True, False]),
                "region": random.choice(["VN", "US", "TH", "ID", "PH"])
            },
            "videos": [],
            "comments": []
        }
        
        base_time = int(time.time())
        
        for i in range(min(max_videos, 10)):
            # Tạo chỉ số tương tác ngẫu nhiên nhưng thực tế
            views = random.randint(1000, 5000000)
            likes = int(views * random.uniform(0.05, 0.15))  # 5-15% tỷ lệ thích
            comments_count = int(views * random.uniform(0.01, 0.05))  # 1-5% tỷ lệ bình luận
            shares = int(views * random.uniform(0.02, 0.08))  # 2-8% tỷ lệ chia sẻ
            
            # Nội dung ngẫu nhiên
            description = random.choice(descriptions_pool)
            hashtags = random.sample(hashtags_pool, k=random.randint(2, 5))
            music = random.choice(music_pool)
            
            video = {
                "id": f"7{random.randint(100000000000000000, 999999999999999999)}",
                "author_id": raw_data["user"]["user_id"],
                "author_name": username,
                "description": f"{description} {' '.join(hashtags)}",
                "create_time": base_time - (i * random.randint(3600, 259200)),  # 1h-3days ago
                "video_url": f"https://tiktok.com/@{username}/video/{7000000000000000000+i}",
                "cover_url": f"https://cdn.tiktok.com/cover/{i}.jpg",
                "duration": random.randint(10, 180),  # 10s - 3min
                "music": music,
                "hashtags": hashtags,
                "mentions": [],
                "is_ad": random.choice([False, False, False, True]),  # 25% ads
                "stats": {
                    "play_count": views,
                    "like_count": likes,
                    "comment_count": comments_count,
                    "share_count": shares,
                    "download_count": int(views * random.uniform(0.01, 0.03)),
                    "forward_count": int(shares * 0.5),
                    "whatsapp_share_count": int(shares * 0.3)
                },
                "metrics": {
                    "engagement_rate": round((likes + comments_count + shares) / views * 100, 2),
                    "like_rate": round(likes / views * 100, 2),
                    "comment_rate": round(comments_count / views * 100, 2),
                    "share_rate": round(shares / views * 100, 2),
                    "completion_rate": round(random.uniform(0.3, 0.9), 2)
                },
                "metadata": {
                    "format": "mp4",
                    "resolution": random.choice(["720p", "1080p", "2k", "4k"]),
                    "fps": random.choice([30, 60]),
                    "codec": "h264",
                    "size_mb": round(random.uniform(5, 50), 2)
                }
            }
            raw_data["videos"].append(video)
            
            # Tạo bình luận mẫu cho mỗi video (tiếng Việt + tiếng Anh)
            comment_templates = [
                "This is amazing! 🔥",
                "Love this content ❤️",
                "Can you do a tutorial?",
                "Where did you get this?",
                "This made my day 😊",
                "So relatable 😂",
                "Need more content like this!",
                "Tag your friends 👥",
                "Part 2 please!",
                "How did you do that? 🤔",
                "Tuyệt vời quá! 🎉",
                "Hay lắm bạn ơi ❤️",
                "Làm tutorial đi bạn",
                "Video rất chất 👍",
                "Đỉnh quá đi mất 🔥"
            ]
            
            num_comments = min(random.randint(5, 30), comments_count)
            for j in range(num_comments):
                comment = {
                    "id": f"c{random.randint(1000000000000000000, 9999999999999999999)}",
                    "video_id": video["id"],
                    "text": random.choice(comment_templates),
                    "author_id": f"user_{random.randint(100000, 999999)}",
                    "author_name": f"user_{random.randint(1000, 9999)}",
                    "author_verified": random.choice([False, False, False, True]),  # 25% verified
                    "create_time": video["create_time"] + random.randint(60, 86400),  # After video
                    "likes": random.randint(0, 1000),
                    "reply_count": random.randint(0, 20),
                    "is_pinned": (j == 0 and random.choice([True, False])),  # First comment might be pinned
                    "language": random.choice(["en", "vi", "th", "id"]),
                    "sentiment": None  # Will be labeled later
                }
                raw_data["comments"].append(comment)
        
        print(f"✅ Collected: {len(raw_data['videos'])} videos, {len(raw_data['comments'])} comments")
        return raw_data
    
    def save_raw_data(self, data: Dict[str, Any], platform: str, identifier: str) -> Path:
        """Lưu dữ liệu thô ra file JSON với tên kèm timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{platform}_{identifier}_{timestamp}_raw.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n?? Saved: {filepath.name} ({len(data.get('videos', []))} videos)")
        return filepath
    
    def collect_and_save(self, platform: str, identifier: str, max_videos: int = 30) -> Dict[str, Any]:
        """Thu thập dữ liệu và lưu ra file - hàm chính để gọi"""
        if platform.lower() == 'tiktok':
            raw_data = self.collect_tiktok(identifier, max_videos)
        else:
            raw_data = self.collect_tiktok(identifier, max_videos)  # Mock for demo
        
        filepath = self.save_raw_data(raw_data, platform, identifier)
        return {"raw_data": raw_data, "filepath": str(filepath), "platform": platform, "identifier": identifier}
