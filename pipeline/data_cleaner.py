"""Data Cleaner - Lọc và làm sạch dữ liệu thô

Module này thực hiện bước 2 trong pipeline:
- Loại bỏ video không hợp lệ (thiếu ID hoặc stats)
- Loại bỏ bình luận trống hoặc quá ngắn
- Chuẩn hóa khoảng trắng trong text bình luận
- Tiền xử lý teen-code, emoji, duplicate (TextPreprocessor)
- Lưu dữ liệu đã làm sạch và dữ liệu bị loại riêng biệt
"""
import json, re, sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

# Thêm thư mục gốc project vào path để import modules
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from modules.text_preprocessor import TextPreprocessor
    _PREPROCESSOR_AVAILABLE = True
except ImportError:
    _PREPROCESSOR_AVAILABLE = False

class DataCleaner:
    def __init__(self, output_cleaned_dir="data/cleaned", output_removed_dir="data/removed", output_report_dir="data/reports",
                 enable_text_preprocessing=True):
        """Khởi tạo DataCleaner với các thư mục đầu ra
        
        Args:
            output_cleaned_dir: Thư mục lưu dữ liệu đã làm sạch
            output_removed_dir: Thư mục lưu dữ liệu bị loại bỏ
            output_report_dir: Thư mục lưu báo cáo làm sạch
            enable_text_preprocessing: Bật tiền xử lý teen-code, emoji, duplicate
        """
        self.output_cleaned_dir = Path(output_cleaned_dir)
        self.output_removed_dir = Path(output_removed_dir)
        self.output_report_dir = Path(output_report_dir)
        self.output_cleaned_dir.mkdir(parents=True, exist_ok=True)
        self.output_removed_dir.mkdir(parents=True, exist_ok=True)
        self.output_report_dir.mkdir(parents=True, exist_ok=True)
        self.min_text_length = 2  # Bình luận phải có ít nhất 2 ký tự
        self.enable_text_preprocessing = enable_text_preprocessing and _PREPROCESSOR_AVAILABLE
        if self.enable_text_preprocessing:
            self._preprocessor = TextPreprocessor(
                normalize_teen=True,
                normalize_emojis=True,
                remove_low_value=True,
                remove_duplicates=True,
            )
        print("Data Cleaner initialized")
    
    def clean_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Làm sạch dữ liệu thô: lọc video và bình luận không hợp lệ
        
        Quy tắc lọc video:
        - Giữ lại: video có ID và có thống kê (stats)
        - Loại bỏ: video thiếu ID hoặc thiếu stats
        
        Quy tắc lọc bình luận:
        - Giữ lại: bình luận có nội dung >= 2 ký tự
        - Loại bỏ: bình luận trống hoặc quá ngắn
        - Chuẩn hóa: gộp khoảng trắng thừa
        """
        print("\nCleaning data...")
        cleaned_videos, removed_videos = [], []
        cleaned_comments, removed_comments = [], []
        
        # Lọc video: giữ lại video có ID và stats hợp lệ
        for video in raw_data.get('videos', []):
            if video.get('id') and video.get('stats'):
                video['title'] = video.get('title') or video.get('description', '')
                cleaned_videos.append(video)
            else:
                video['removal_reason'] = 'invalid'  # Đánh dấu lý do loại bỏ
                removed_videos.append(video)
        
        # Lọc bình luận: loại bỏ bình luận trống hoặc quá ngắn
        for comment in raw_data.get('comments', []):
            text = (comment.get('text') or '').strip()
            if text and len(text) >= self.min_text_length:
                comment['text'] = re.sub(r'\s+', ' ', text)  # Chuẩn hóa khoảng trắng
                cleaned_comments.append(comment)
            else:
                comment['removal_reason'] = 'empty_or_short'  # Đánh dấu lý do loại bỏ
                removed_comments.append(comment)
        
        # Tiền xử lý nâng cao: teen-code, emoji, duplicate
        preprocess_stats = {}
        if self.enable_text_preprocessing and cleaned_comments:
            result = self._preprocessor.process_comments(cleaned_comments)
            preprocess_stats = result["stats"]
            removed_comments.extend(result["removed_low_value"])
            removed_comments.extend(result["removed_duplicate"])
            cleaned_comments = result["processed"]
            print(f"Preprocessing: {preprocess_stats['kept']} kept, "
                  f"{preprocess_stats['removed_low_value']} low-value, "
                  f"{preprocess_stats['removed_duplicate']} duplicate removed")
        
        print(f"Videos: {len(cleaned_videos)} kept, {len(removed_videos)} removed")
        print(f"Comments: {len(cleaned_comments)} kept, {len(removed_comments)} removed")
        
        # Tạo dữ liệu đã làm sạch kèm thống kê quá trình
        cleaned_data = {
            "metadata": raw_data.get('metadata', {}),
            "user": raw_data.get('user'),
            "videos": cleaned_videos,
            "comments": cleaned_comments,
            "cleaning_info": {
                "cleaned_at": datetime.now().isoformat(),
                "original_videos": len(raw_data.get('videos', [])),
                "cleaned_videos": len(cleaned_videos),
                "original_comments": len(raw_data.get('comments', [])),
                "cleaned_comments": len(cleaned_comments),
                "text_preprocessing_enabled": self.enable_text_preprocessing,
                "preprocess_stats": preprocess_stats,
            }
        }
        
        # Lưu riêng dữ liệu bị loại để kiểm tra lại nếu cần
        removed_data = {
            "metadata": raw_data.get('metadata', {}),
            "videos": removed_videos,
            "comments": removed_comments
        }
        
        return {"cleaned_data": cleaned_data, "removed_data": removed_data, "stats": cleaned_data['cleaning_info']}
    
    def save_cleaned_data(self, cleaned_data, removed_data, platform, identifier):
        """Lưu dữ liệu đã làm sạch và dữ liệu bị loại ra file JSON riêng biệt"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        cleaned_path = self.output_cleaned_dir / f"{platform}_{identifier}_{ts}_cleaned.json"
        removed_path = self.output_removed_dir / f"{platform}_{identifier}_{ts}_removed.json"
        
        with open(cleaned_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        with open(removed_path, 'w', encoding='utf-8') as f:
            json.dump(removed_data, f, ensure_ascii=False, indent=2)
        
        print(f"\nSaved: {cleaned_path.name}, {removed_path.name}")
        return {"cleaned": str(cleaned_path), "removed": str(removed_path)}
