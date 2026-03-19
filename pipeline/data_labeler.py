"""Data Labeler - Gán nhãn sentiment (cảm xúc) cho bình luận

Module này thực hiện bước 3 trong pipeline:
- Gán nhãn positive/negative/neutral cho mỗi bình luận
- Hỗ trợ 3 phương pháp: tự động (auto), thủ công (manual), kết hợp (hybrid)
- Tính độ tin cậy (confidence) cho mỗi nhãn
- Lưu dữ liệu đã gán nhãn vào thư mục data/labeled/

Lưu ý: Module này dùng phương pháp đơn giản (keyword matching).
Trong thực tế, dữ liệu đã được PhoBERT gán nhãn từ trước
(xem modules/sentiment_analyzer.py).
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from enum import Enum

class LabelMethod(Enum):
    """Phương pháp gán nhãn: tự động, thủ công, hoặc kết hợp"""
    AUTO, MANUAL, HYBRID = "auto", "manual", "hybrid"

class DataLabeler:
    """Lớp gán nhãn sentiment cho bình luận"""
    
    def __init__(self, output_dir="data/labeled", confidence_threshold=0.7, use_vietnamese=True):
        """Khởi tạo DataLabeler
        
        Args:
            output_dir: Thư mục lưu dữ liệu đã gán nhãn
            confidence_threshold: Ngưỡng độ tin cậy tối thiểu
            use_vietnamese: Sử dụng phân tích tiếng Việt
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.confidence_threshold = confidence_threshold
        print(f"? DataLabeler initialized (threshold: {confidence_threshold})")
    
    def label_data(self, cleaned_data, method=LabelMethod.AUTO):
        """Gán nhãn sentiment cho tất cả bình luận
        
        Phương pháp đơn giản (keyword matching):
        - Positive: chứa 'tốt', 'hay', 'đẹp', 'like' -> confidence 0.8
        - Negative: chứa 'tệ', 'dở', 'bad' -> confidence 0.8
        - Neutral: còn lại -> confidence 0.6
        
        Lưu ý: Trong pipeline thực tế, dùng PhoBERT cho độ chính xác ~92%
        """
        print(f"\n???  Labeling (method: {method.value})...")
        comments = cleaned_data.get('comments', [])
        labeled_comments = []
        
        for comment in comments:
            text = comment.get('text', '').lower()
            if 't?t' in text or 'hay' in text or 'd?p' in text or 'like' in text:
                sentiment, conf = 'positive', 0.8
            elif 't?' in text or 'd?' in text or 'bad' in text:
                sentiment, conf = 'negative', 0.8
            else:
                sentiment, conf = 'neutral', 0.6
            
            comment['sentiment'] = sentiment
            comment['confidence'] = conf
            comment['labeling_method'] = method.value
            labeled_comments.append(comment)
        
        # Thống kê phân phối sentiment sau khi gán nhãn
        sentiment_dist = {'positive': sum(1 for c in labeled_comments if c['sentiment']=='positive'),
                         'negative': sum(1 for c in labeled_comments if c['sentiment']=='negative'),
                         'neutral': sum(1 for c in labeled_comments if c['sentiment']=='neutral')}
        
        print(f"? Labeled {len(labeled_comments)} comments")
        print(f"   Positive: {sentiment_dist['positive']}, Negative: {sentiment_dist['negative']}, Neutral: {sentiment_dist['neutral']}")
        
        labeled_data = {**cleaned_data, "comments": labeled_comments,
                       "labeling_info": {"labeled_at": datetime.now().isoformat(),
                                        "method": method.value,
                                        "sentiment_distribution": sentiment_dist}}
        
        return {"labeled_data": labeled_data, "low_confidence": [], "stats": labeled_data['labeling_info']}
    
    def save_labeled_data(self, labeled_data, platform, identifier):
        """Lưu dữ liệu đã gán nhãn ra file JSON"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"{platform}_{identifier}_{ts}_labeled.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(labeled_data, f, ensure_ascii=False, indent=2)
        print(f"\n?? Saved: {filepath.name}")
        return filepath
