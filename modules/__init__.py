"""
Gói Modules - Các module phân tích YouTube & TikTok

Các module chính:
- YouTubeScraper: Thu thập dữ liệu YouTube (dùng YouTube Data API v3)
- TikTokScraper: Thu thập dữ liệu TikTok qua Official API (cần OAuth)
- TikTokAPICollector: Thu thập TikTok qua thư viện không chính thức
- SentimentAnalyzer: Phân tích cảm xúc bình luận (PhoBERT, underthesea, VADER)
- MetricsAnalyzer: Phân tích chỉ số tương tác (engagement metrics)
- GeminiSentimentAnalyzer: Phân tích sentiment dùng Google Gemini AI
"""

from .youtube_scraper import YouTubeScraper
from .tiktok_scraper import TikTokScraper
from .sentiment_analyzer import SentimentAnalyzer
from .metrics_analyzer import MetricsAnalyzer
from .tiktok_api_scraper import TikTokAPICollector
from .gemini_sentiment import GeminiSentimentAnalyzer, get_gemini_analyzer

__all__ = [
    'YouTubeScraper',
    'TikTokScraper',
    'SentimentAnalyzer',
    'MetricsAnalyzer',
    'TikTokAPICollector',
    'GeminiSentimentAnalyzer',
    'get_gemini_analyzer',
]
