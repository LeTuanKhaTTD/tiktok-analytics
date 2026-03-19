"""Pipeline Orchestrator - Bộ điều khiển chính của pipeline

Module này điều phối toàn bộ 5 bước của pipeline:
1. COLLECT: Thu thập dữ liệu thô từ TikTok
2. CLEAN: Làm sạch dữ liệu (loại video/bình luận không hợp lệ)
3. LABEL: Gán nhãn sentiment (positive/negative/neutral)
4. VALIDATE: Kiểm tra chất lượng dữ liệu đã gán nhãn
5. EXPORT: Xuất ra nhiều định dạng (JSON, CSV, Excel, Parquet)
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from .data_collector import DataCollector
from .data_cleaner import DataCleaner
from .data_labeler import DataLabeler, LabelMethod
from .data_validator import DataValidator
from .data_exporter import DataExporter

class DataPipeline:
    """Bộ điều khiển chính - chạy tuần tự 5 bước pipeline"""
    
    def __init__(self, data_dir="data", confidence_threshold=0.7, use_vietnamese=True):
        """Khởi tạo pipeline với tất cả các module con
        
        Args:
            data_dir: Thư mục gốc chứa dữ liệu
            confidence_threshold: Ngưỡng độ tin cậy tối thiểu
            use_vietnamese: Sử dụng phân tích tiếng Việt
        """
        self.data_dir = data_dir
        self.collector = DataCollector(f"{data_dir}/raw")
        self.cleaner = DataCleaner(f"{data_dir}/cleaned", f"{data_dir}/removed", f"{data_dir}/reports")
        self.labeler = DataLabeler(f"{data_dir}/labeled", confidence_threshold, use_vietnamese)
        self.validator = DataValidator(f"{data_dir}/validated", f"{data_dir}/reports", confidence_threshold)
        self.exporter = DataExporter(f"{data_dir}/export")
        self.results = {}
        
        print(f"\n{'='*70}")
        print(f"?? DATA PIPELINE INITIALIZED")
        print(f"{'='*70}\n")
    
    def run(self, platform, identifier, max_videos=30, labeling_method="auto", export_formats=None, resume_from_stage=None):
        """Chạy toàn bộ pipeline từ đầu đến cuối
        
        Args:
            platform: Nền tảng (tiktok/youtube)
            identifier: Tên tài khoản cần phân tích
            max_videos: Số video tối đa thu thập
            labeling_method: Phương pháp gán nhãn ('auto', 'manual', 'hybrid')
            export_formats: Danh sách định dạng xuất
            resume_from_stage: Tiếp tục từ bước nào (nếu pipeline bị gán đoạn)
        """
        start_time = datetime.now()
        print(f"{'='*70}")
        print(f"?? STARTING PIPELINE")
        print(f"{'='*70}")
        print(f"Platform: {platform}, ID: {identifier}, Videos: {max_videos}")
        print(f"{'='*70}\n")
        
        try:
            # Bước 1: Thu thập dữ liệu thô
            print(f"{'-'*70}")
            print(f"Stage 1/5: COLLECT")
            print(f"{'-'*70}")
            result_collect = self.collector.collect_and_save(platform, identifier, max_videos)
            self.results['collect'] = result_collect
            
            # Bước 2: Làm sạch dữ liệu
            print(f"\n{'-'*70}")
            print(f"Stage 2/5: CLEAN")
            print(f"{'-'*70}")
            result_clean = self.cleaner.clean_data(self.results['collect']['raw_data'])
            paths_clean = self.cleaner.save_cleaned_data(result_clean['cleaned_data'], 
                                                         result_clean['removed_data'],
                                                         platform, identifier)
            self.results['clean'] = {**result_clean, 'paths': paths_clean}
            
            # Bước 3: Gán nhãn sentiment
            print(f"\n{'-'*70}")
            print(f"Stage 3/5: LABEL")
            print(f"{'-'*70}")
            method = LabelMethod.AUTO if labeling_method=='auto' else LabelMethod.MANUAL if labeling_method=='manual' else LabelMethod.HYBRID
            result_label = self.labeler.label_data(self.results['clean']['cleaned_data'], method)
            filepath_label = self.labeler.save_labeled_data(result_label['labeled_data'], platform, identifier)
            self.results['label'] = {**result_label, 'filepath': str(filepath_label)}
            
            # Bước 4: Kiểm tra chất lượng
            print(f"\n{'-'*70}")
            print(f"Stage 4/5: VALIDATE")
            print(f"{'-'*70}")
            result_validate = self.validator.validate_data(self.results['label']['labeled_data'])
            paths_validate = self.validator.save_validated_data(result_validate['validated_data'],
                                                               result_validate['issues'],
                                                               platform, identifier)
            self.results['validate'] = {**result_validate, 'paths': paths_validate}
            
            # Bước 5: Xuất dữ liệu ra nhiều định dạng
            print(f"\n{'-'*70}")
            print(f"Stage 5/5: EXPORT")
            print(f"{'-'*70}")
            exported = self.exporter.export_all(self.results['validate']['validated_data'],
                                               platform, identifier, export_formats)
            self.results['export'] = {'files': exported}
            
            duration = (datetime.now() - start_time).total_seconds()
            
            print(f"\n{'='*70}")
            print(f"? PIPELINE COMPLETED!")
            print(f"{'='*70}")
            print(f"Duration: {duration:.1f}s")
            print(f"\n?? SUMMARY:")
            if 'clean' in self.results:
                print(f"   Videos: {self.results['clean']['stats']['cleaned_videos']}")
            if 'label' in self.results:
                dist = self.results['label']['stats']['sentiment_distribution']
                print(f"   Sentiment: +{dist['positive']} / -{dist['negative']} / ={dist['neutral']}")
            print(f"{'='*70}\n")
            
            return {"success": True, "results": self.results, "duration_seconds": duration}
            
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"? PIPELINE FAILED: {e}")
            print(f"{'='*70}\n")
            return {"success": False, "error": str(e), "results": self.results}
