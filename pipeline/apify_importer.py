"""Apify Profile Data Import - Nhập dữ liệu TikTok từ Apify

Module này thực hiện bước 1 trong pipeline (Thu thập dữ liệu):
- Đọc file JSON xuất từ Apify TikTok Scraper
- Chuyển đổi cấu trúc phẳng (dấu chấm) sang cấu trúc pipeline chuẩn
- Trích xuất đầy đủ thống kê: views, likes, comments, shares, saves
- Tính engagement rate cho từng video
- Lưu dữ liệu thô vào thư mục data/raw/
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class ApifyProfileImporter:
    """Lớp nhập dữ liệu từ Apify TikTok Scraper
    
    Apify là dịch vụ cloud scraping, xuất dữ liệu dạng phẳng với dấu chấm:
    Ví dụ: 'authorMeta.name', 'diggCount', 'playCount', ...
    
    Module này chuyển đổi sang cấu trúc chuẩn của pipeline.
    """
    def __init__(self, output_dir: str = "data/raw"):
        """Khởi tạo importer với thư mục lưu dữ liệu thô"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📥 ApifyProfileImporter initialized: {self.output_dir}")
    
    def extract_video_id(self, url: str) -> str:
        """Trích xuất video ID từ URL TikTok
        Ví dụ: https://tiktok.com/@user/video/123456 -> 123456
        """
        match = re.search(r'/video/(\d+)', url)
        return match.group(1) if match else url
    
    def import_from_apify(self, filepath: str) -> Dict[str, Any]:
        """
        Nhập dữ liệu từ file JSON của Apify TikTok Scraper
        
        Cấu trúc Apify dùng dấu chấm phân cấp (flat structure):
        {
          "authorMeta.name": "travinhuniversity",   # Tên tài khoản
          "text": "Mô tả video",                     # Nội dung mô tả
          "diggCount": 32800,                        # Số lượt thích
          "shareCount": 4969,                        # Số lượt chia sẻ
          "playCount": 1600000,                      # Số lượt xem
          "commentCount": 386,                       # Số bình luận
          "collectCount": 500,                       # Số lượt lưu
          "webVideoUrl": "https://...",              # Link video
          ...
        }
        """
        print(f"\n📂 Loading Apify data from: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            apify_videos = json.load(f)
        
        if not isinstance(apify_videos, list):
            raise ValueError("Dữ liệu Apify phải là một danh sách (list) các video")
        
        if not apify_videos:
            raise ValueError("Không tìm thấy video nào trong dữ liệu Apify")
        
        # Lấy tên tài khoản từ video đầu tiên
        username = apify_videos[0].get('authorMeta.name', 'unknown')
        
        # Chuyển đổi sang cấu trúc chuẩn của pipeline
        raw_data = {
            "metadata": {
                "platform": "tiktok",
                "identifier": username,
                "collected_at": datetime.now().isoformat(),
                "collector_version": "4.0.0-apify-profile",
                "source": "apify",
                "source_file": str(filepath),
                "total_videos_imported": len(apify_videos)
            },
            "user": {
                "username": username,
                "user_id": f"apify_{username}",
                "nickname": username.replace("_", " ").title(),
                "verified": False,
                "total_videos": len(apify_videos)
            },
            "videos": [],
            "comments": []
        }
        
        # Chuyển đổi từng video từ cấu trúc Apify sang cấu trúc pipeline
        for video in apify_videos:
            video_url = video.get('webVideoUrl', '')
            video_id = self.extract_video_id(video_url)
            
            # Trích xuất hashtag từ mô tả video
            text = video.get('text', '')
            hashtags = re.findall(r'#(\w+)', text)
            
            # Tạo entry video với ĐẦY ĐỦ thống kê tương tác
            video_entry = {
                "id": video_id,
                "author_name": video.get('authorMeta.name', ''),
                "author_id": video.get('authorMeta.id', ''),
                "description": text,
                "create_time": video.get('createTimeISO', ''),
                "duration": video.get('videoMeta.duration', 0),
                "video_url": video_url,
                "cover_url": video.get('covers.default', ''),
                "hashtags": hashtags,
                "is_ad": False,
                "music": {
                    "title": video.get('musicMeta.musicName', ''),
                    "author": video.get('musicMeta.musicAuthor', ''),
                    "id": video.get('musicMeta.musicId', ''),
                    "original": video.get('musicMeta.musicOriginal', False)
                },
                "stats": {
                    "play_count": video.get('playCount', 0),        # ✅ Views
                    "like_count": video.get('diggCount', 0),        # ✅ Video Likes
                    "comment_count": video.get('commentCount', 0),  # ✅ Comments
                    "share_count": video.get('shareCount', 0),      # ✅ Shares
                    "collect_count": video.get('collectCount', 0)   # ✅ Saves/Collections
                },
                "metadata": {
                    "resolution": "",
                    "ratio": "",
                    "size_mb": 0
                }
            }
            
            # Tính các chỉ số tương tác (engagement metrics)
            play_count = video_entry['stats']['play_count']
            if play_count > 0:
                # Tổng tương tác = likes + comments + shares
                total_engagement = (
                    video_entry['stats']['like_count'] + 
                    video_entry['stats']['comment_count'] + 
                    video_entry['stats']['share_count']
                )
                video_entry['metrics'] = {
                    "engagement_rate": round(total_engagement / play_count * 100, 2),
                    "like_rate": round(video_entry['stats']['like_count'] / play_count * 100, 2),
                    "comment_rate": round(video_entry['stats']['comment_count'] / play_count * 100, 2),
                    "share_rate": round(video_entry['stats']['share_count'] / play_count * 100, 2),
                    "collect_rate": round(video_entry['stats']['collect_count'] / play_count * 100, 2)
                }
            else:
                video_entry['metrics'] = {
                    "engagement_rate": 0,
                    "like_rate": 0,
                    "comment_rate": 0,
                    "share_rate": 0,
                    "collect_rate": 0
                }
            
            raw_data["videos"].append(video_entry)
        
        # Tính tổng các chỉ số của toàn bộ kênh
        total_plays = sum(v['stats']['play_count'] for v in raw_data['videos'])
        total_likes = sum(v['stats']['like_count'] for v in raw_data['videos'])
        total_comments = sum(v['stats']['comment_count'] for v in raw_data['videos'])
        total_shares = sum(v['stats']['share_count'] for v in raw_data['videos'])
        
        print(f"✅ Loaded: {len(raw_data['videos'])} videos with FULL stats")
        print(f"📊 Total plays: {total_plays:,}")
        print(f"❤️  Total likes: {total_likes:,}")
        print(f"💬 Total comments: {total_comments:,}")
        print(f"🔄 Total shares: {total_shares:,}")
        
        # Lưu tổng các chỉ số vào metadata của user
        raw_data['user']['total_plays'] = total_plays
        raw_data['user']['total_likes'] = total_likes
        raw_data['user']['total_comments'] = total_comments
        raw_data['user']['total_shares'] = total_shares
        
        return raw_data
    
    def save_raw_data(self, data: Dict[str, Any], platform: str, identifier: str) -> Path:
        """Lưu dữ liệu thô ra file JSON với tên kèm timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{platform}_{identifier}_{timestamp}_raw_apify.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Saved: {filepath.name}")
        return filepath
    
    def import_and_save(self, source_file: str, platform: str = "tiktok") -> Dict[str, Any]:
        """Nhập dữ liệu từ file Apify và lưu vào cấu trúc pipeline
        
        Đây là hàm chính để chạy: đọc file gốc -> chuyển đổi -> lưu file
        """
        raw_data = self.import_from_apify(source_file)
        
        identifier = raw_data['user']['username']
        filepath = self.save_raw_data(raw_data, platform, identifier)
        
        return {
            "raw_data": raw_data,
            "filepath": str(filepath),
            "platform": platform,
            "identifier": identifier
        }
