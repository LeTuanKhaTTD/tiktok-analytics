"""Data Validator - Kiểm tra chất lượng dữ liệu

Module này thực hiện bước 4 trong pipeline:
- Kiểm tra bình luận đã được gán nhãn sentiment chưa
- Kiểm tra tỷ lệ bình luận có độ tin cậy thấp (low confidence)
- Đánh dấu dữ liệu đạt/không đạt (passed/failed)
- Lưu dữ liệu đã xác thực vào thư mục data/validated/
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class DataValidator:
    """Lớp kiểm tra chất lượng dữ liệu sau khi gán nhãn"""
    
    def __init__(self, output_validated_dir="data/validated", output_report_dir="data/reports", min_confidence=0.6, max_neutral_ratio=0.5):
        """Khởi tạo DataValidator
        
        Args:
            output_validated_dir: Thư mục lưu dữ liệu đã xác thực
            output_report_dir: Thư mục lưu báo cáo xác thực
            min_confidence: Ngưỡng confidence tối thiểu (mặc định 0.6)
            max_neutral_ratio: Tỷ lệ neutral tối đa chấp nhận được
        """
        self.output_validated_dir = Path(output_validated_dir)
        self.output_report_dir = Path(output_report_dir)
        self.output_validated_dir.mkdir(parents=True, exist_ok=True)
        self.output_report_dir.mkdir(parents=True, exist_ok=True)
        self.min_confidence = min_confidence
        print(f"? DataValidator initialized")
    
    def validate_data(self, labeled_data):
        """Kiểm tra chất lượng dữ liệu đã gán nhãn
        
        Kiểm tra:
        - Số bình luận bị thiếu sentiment -> lỗi (error)
        - Tỷ lệ bình luận có confidence thấp > 30% -> cảnh báo (warning)
        """
        print(f"\n? Validating...")
        comments = labeled_data.get('comments', [])
        issues = []
        
        # Kiểm tra bình luận thiếu nhãn sentiment
        missing_sentiment = sum(1 for c in comments if not c.get('sentiment'))
        # Kiểm tra bình luận có độ tin cậy thấp
        low_conf = sum(1 for c in comments if c.get('confidence', 1) < self.min_confidence)
        
        if missing_sentiment > 0:
            issues.append({"severity": "error", "message": f"{missing_sentiment} missing sentiment"})
        if low_conf > len(comments) * 0.3:
            issues.append({"severity": "warning", "message": f"{low_conf} low_confidence"})
        
        # Kết quả: đạt nếu không có lỗi nghiêm trọng (error)
        passed = len([i for i in issues if i['severity']=='error']) == 0
        
        print(f"{'?' if passed else '?'} Validation {'passed' if passed else 'failed'} ({len(issues)} issues)")
        
        validated_data = {**labeled_data, 
                         "validation_info": {"validated_at": datetime.now().isoformat(),
                                           "passed": passed,
                                           "error_count": len([i for i in issues if i['severity']=='error'])}}
        
        return {"validated_data": validated_data, "issues": issues, "passed": passed, "stats": validated_data['validation_info']}
    
    def save_validated_data(self, validated_data, issues, platform, identifier):
        """Lưu dữ liệu đã xác thực ra file JSON"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_validated_dir / f"{platform}_{identifier}_{ts}_validated.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(validated_data, f, ensure_ascii=False, indent=2)
        print(f"\n?? Saved: {filepath.name}")
        return {"validated": str(filepath)}
