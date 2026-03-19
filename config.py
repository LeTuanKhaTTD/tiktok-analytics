"""
config.py - Cấu hình toàn cục cho TikTok & YouTube Analytics

Chứa:
- API keys và credentials (YouTube API, TikTok tokens)
- File paths và directories (data/, reports/, archived/)
- Model settings (PhoBERT, underthesea, VADER)
- Thresholds và limits (video count, comment count)
- Analysis parameters (sentiment confidence, metrics)

Usage:
    from config import YOUTUBE_API_KEY, DATA_DIR, USE_TRANSFORMERS
    
    # Access settings
    api_key = YOUTUBE_API_KEY  # or os.getenv('YOUTUBE_API_KEY')
    use_phobert = USE_TRANSFORMERS
    
Environment Variables:
- YOUTUBE_API_KEY: Your YouTube Data API v3 key
- OPENAI_API_KEY: (optional) For GPT-based analysis
- TIKTOK_SESSION_ID: (optional) For TikTok API access

Security:
- NEVER commit API keys to git
- Use .env file for local development
- Set environment variables in production

Author: TikTok Analytics Team
Created: 2026-03-01
Updated: 2026-03-05
"""

# Configuration file for YouTube Analytics

# YouTube API Settings
YOUTUBE_API_KEY = None  # Set via environment variable YOUTUBE_API_KEY
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# Scraping Settings
DEFAULT_VIDEO_COUNT = 30
DEFAULT_COMMENTS_PER_VIDEO = 50
MAX_VIDEO_COUNT = 200
MAX_COMMENTS_PER_VIDEO = 500

# Sentiment Analysis Settings
USE_VIETNAMESE = True    # Use Vietnamese models (PhoBERT, underthesea)
USE_TRANSFORMERS = False  # Use PhoBERT (slower but 85-90% accuracy vs underthesea 70-75%)
SENTIMENT_CONFIDENCE_THRESHOLD = 0.5
SUPPORTED_LANGUAGES = ['en', 'vi', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko']

# Metrics Settings
ENGAGEMENT_THRESHOLD_HIGH = 5.0  # % engagement rate considered high
ENGAGEMENT_THRESHOLD_LOW = 2.0   # % engagement rate considered low
VIRALITY_THRESHOLD = 0.01        # Virality score threshold

# Visualization Settings
FIGURE_DPI = 300
FIGURE_SIZE_DEFAULT = (15, 10)

# Output Settings
OUTPUT_DIR = 'data'
REPORTS_DIR = 'reports'
SAVE_RAW_DATA = True
SAVE_SENTIMENT_DATA = True
SAVE_METRICS_DATA = True
EXPORT_CSV = True
GENERATE_VISUALIZATIONS = True

# File Settings
FILE_ENCODING = 'utf-8'

# YouTube API Quota
# Free tier: 10,000 units/day
# Search: 100 units, Videos.list: 1 unit, Comments: 1 unit
YOUTUBE_QUOTA_DAILY_LIMIT = 10000

# ============================================================================
# GEMINI AI SETTINGS (Added 2026-03-11)
# ============================================================================
# Google Gemini API for advanced sentiment analysis
GEMINI_API_KEY = None  # Set via environment variable GEMINI_API_KEY
GEMINI_MODEL = "gemini-2.0-flash"  # Free tier model
GEMINI_ENABLE_CACHE = True
GEMINI_MAX_RETRIES = 5
GEMINI_BASE_DELAY = 2.0  # seconds between requests
GEMINI_BATCH_SIZE = 50  # process in batches to avoid rate limits
