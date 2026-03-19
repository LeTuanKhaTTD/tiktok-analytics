"""Data Importer - Nhập dữ liệu TikTok từ file JSON có sẵn

Module này nhập dữ liệu từ file tong_hop_comment.json:
- Đọc file JSON chứa video + comments đã phân tích sentiment
- Chuyển đổi sang cấu trúc chuẩn của pipeline
- Giữ nguyên nhãn sentiment đã được PhoBERT gán
- Lưu dữ liệu thô vào thư mục data/raw/
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class DataImporter:
    """Lớp nhập dữ liệu từ file JSON có sẵn (tong_hop_comment.json)"""
    
    def __init__(self, output_dir: str = "data/raw"):
        """Khởi tạo DataImporter với thư mục lưu dữ liệu thô"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📥 DataImporter initialized: {self.output_dir}")
    
    def import_from_file(self, filepath: str) -> Dict[str, Any]:
        """Nhập dữ liệu từ file tong_hop_comment.json
        
        File này chứa:
        - username: tên tài khoản TikTok
        - videos: danh sách video kèm comments đã gán sentiment
        - model: tên model đã dùng (PhoBERT)
        - accuracy: độ chính xác của model
        """
        print(f"\n📂 Loading data from: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        
        # Lấy metadata từ file gốc
        username = source_data.get('username', '@travinhuniversity').replace('@', '')
        
        # Chuyển đổi sang cấu trúc chuẩn của pipeline
        raw_data = {
            "metadata": {
                "platform": "tiktok",
                "identifier": username,
                "collected_at": datetime.now().isoformat(),
                "collector_version": "3.0.0-real-data",
                "source": "imported",
                "source_file": str(filepath),
                "original_analyzed_at": source_data.get('analyzed_at'),
                "original_model": source_data.get('model'),
                "accuracy": source_data.get('accuracy')
            },
            "user": {
                "username": username,
                "user_id": f"imported_{username}",
                "nickname": username.replace("_", " ").title(),
                "total_videos": source_data.get('total_videos', 0),
                "total_comments": source_data.get('total_comments', 0),
                "total_likes": source_data.get('total_likes', 0)
            },
            "videos": [],
            "comments": []
        }
        
        # Chuyển đổi videos và comments sang cấu trúc mới
        for video in source_data.get('videos', []):
            video_id = video.get('video_id')
            video_url = video.get('video_url')
            comments_count = video.get('comments_count', 0)
            
            # Tạo entry video
            video_entry = {
                "id": video_id,
                "video_url": video_url,
                "comments_count": comments_count,
                "total_likes": video.get('total_likes', 0),
                "avg_likes_per_comment": video.get('avg_likes_per_comment', 0),
                "stats": {
                    "comment_count": comments_count,
                    "total_comment_likes": video.get('total_likes', 0)
                }
            }
            raw_data["videos"].append(video_entry)
            
            # Chuyển đổi comments, giữ nguyên sentiment đã được PhoBERT gán
            for comment in video.get('comments', []):
                comment_entry = {
                    "id": f"imported_{len(raw_data['comments'])}",
                    "video_id": video_id,
                    "text": comment.get('text', ''),
                    "author_name": comment.get('author', ''),
                    "author_id": comment.get('author', ''),
                    "author_verified": False,
                    "create_time": comment.get('created_at', ''),
                    "likes": comment.get('likes', 0),
                    "reply_count": 0,
                    "is_pinned": False,
                    "language": comment.get('language', 'vi'),
                    "sentiment": comment.get('sentiment'),  # Already has sentiment!
                    "confidence": comment.get('confidence', 0),
                    "labeling_method": "phobert"  # From PhoBERT model
                }
                raw_data["comments"].append(comment_entry)
        
        print(f"✅ Loaded: {len(raw_data['videos'])} videos, {len(raw_data['comments'])} comments")
        print(f"📊 Sentiment: {source_data.get('global_sentiment_summary', {})}")
        
        return raw_data
    
    def save_raw_data(self, data: Dict[str, Any], platform: str, identifier: str) -> Path:
        """Lưu dữ liệu thô ra file JSON với tên kèm timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{platform}_{identifier}_{timestamp}_raw_imported.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Saved: {filepath.name}")
        return filepath
    
    def import_and_save(self, source_file: str, platform: str = "tiktok") -> Dict[str, Any]:
        """Nhập dữ liệu từ file và lưu vào cấu trúc pipeline
        
        Đây là hàm chính để chạy: đọc file gốc -> chuyển đổi -> lưu file
        """
        raw_data = self.import_from_file(source_file)
        
        identifier = raw_data['user']['username']
        filepath = self.save_raw_data(raw_data, platform, identifier)
        
        return {
            "raw_data": raw_data,
            "filepath": str(filepath),
            "platform": platform,
            "identifier": identifier
        }
