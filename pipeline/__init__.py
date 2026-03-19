"""
Gói Pipeline - Xử lý dữ liệu TikTok theo 5 bước

Các module:
- DataCollector: Thu thập dữ liệu thô (demo/mock)
- DataCleaner: Làm sạch dữ liệu (loại bỏ video/bình luận không hợp lệ)
- DataLabeler: Gán nhãn sentiment cho bình luận
- DataValidator: Kiểm tra chất lượng dữ liệu đã xử lý
- DataExporter: Xuất dữ liệu ra nhiều định dạng (JSON, CSV, Excel, Parquet)
- DataPipeline: Bộ điều khiển chạy tuần tự 5 bước
"""

from .data_collector import DataCollector
from .data_cleaner import DataCleaner
from .data_labeler import DataLabeler
from .data_validator import DataValidator
from .data_exporter import DataExporter
from .pipeline_orchestrator import DataPipeline

__all__ = [
    'DataCollector',
    'DataCleaner',
    'DataLabeler',
    'DataValidator',
    'DataExporter',
    'DataPipeline'
]

__version__ = '1.0.0'
