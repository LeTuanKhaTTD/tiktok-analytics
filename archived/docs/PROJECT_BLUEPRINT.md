# 🎯 PROJECT BLUEPRINT - Hướng dẫn hoàn chỉnh cho AI Assistant

> **Mục đích**: Document này chứa TẤT CẢ thông tin cần thiết để Claude 4.6 (hoặc AI assistant khác) có thể tái tạo lại TOÀN BỘ dự án từ đầu đến cuối.

---

## 📋 MỤC LỤC

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Yêu cầu kỹ thuật](#2-yêu-cầu-kỹ-thuật)
3. [Cấu trúc thư mục](#3-cấu-trúc-thư-mục)
4. [Module 1: YouTube Scraper](#4-module-1-youtube-scraper)
5. [Module 2: TikTok Scraper](#5-module-2-tiktok-scraper)
6. [Module 3: Sentiment Analyzer](#6-module-3-sentiment-analyzer)
7. [Module 4: Metrics Analyzer](#7-module-4-metrics-analyzer)
8. [Configuration File](#8-configuration-file)
9. [Demo Scripts](#9-demo-scripts)
10. [OAuth Helper](#10-oauth-helper)
11. [Hướng dẫn triển khai](#11-hướng-dẫn-triển-khai)
12. [Testing & Validation](#12-testing--validation)
13. [Yêu cầu đặc biệt](#13-yêu-cầu-đặc-biệt)

---

## 1. TỔNG QUAN DỰ ÁN

### 1.1 Mục tiêu chính

Tạo một hệ thống phân tích social media analytics **ĐA NỀN TẢNG** (dual-platform) với khả năng:

1. **Thu thập dữ liệu** từ YouTube và TikTok
2. **Phân tích sentiment** (cảm xúc) từ comments - **CHUYÊN cho tiếng Việt**
3. **Tính toán metrics** (engagement rate, virality score, interaction rate, etc.)
4. **Tạo visualizations** (biểu đồ PNG + HTML interactive)
5. **Sinh báo cáo** tổng hợp với insights và recommendations

### 1.2 Đặc điểm nổi bật

- ✅ **Dual-platform**: Hỗ trợ cả YouTube và TikTok
- ✅ **Vietnamese-first**: Phân tích sentiment tiếng Việt chính xác cao (85-90%)
- ✅ **Modular design**: 4 modules độc lập, dễ mở rộng
- ✅ **Production-ready**: OAuth 2.0, error handling, quota management
- ✅ **Rich visualizations**: 4 loại biểu đồ (sentiment, engagement, trends, correlation)

### 1.3 Use cases

1. **Content creators**: Phân tích hiệu quả nội dung, tìm trending topics
2. **Marketers**: Đo lường campaign performance trên nhiều platform
3. **Researchers**: Nghiên cứu Vietnamese social media behavior
4. **Businesses**: Monitor brand sentiment, competitor analysis

---

## 2. YÊU CẦU KỸ THUẬT

### 2.1 Python Environment

```
Python: 3.11+ (recommended)
Virtual Environment: venv hoặc conda
OS: Windows/Linux/macOS
```

### 2.2 Dependencies (requirements.txt)

```txt
# YouTube Analytics Dependencies

# YouTube API
google-api-python-client==2.110.0
google-auth==2.25.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0

# Web Scraping (if needed)
beautifulsoup4==4.12.2
requests==2.31.0

# Data Processing
pandas==2.1.4
numpy==1.26.2

# Sentiment Analysis
transformers==4.36.0
torch==2.1.1
textblob==0.17.1
vaderSentiment==3.3.2

# Vietnamese NLP (Chuyên cho tiếng Việt)
underthesea==6.7.0
vncorenlp==1.0.3
pyvi==0.1.1

# Visualization
matplotlib==3.8.2
seaborn==0.13.0
plotly==5.18.0

# Natural Language Processing
nltk==3.8.1
langdetect==1.0.9

# Configuration
python-dotenv==1.0.0
pyyaml==6.0.1

# Utilities
tqdm==4.66.1
openpyxl==3.1.2
pillow==10.1.0
```

### 2.3 API Credentials

**YouTube Data API v3**
- API Key: `AIzaSyClfAZjwp8JMSH86ZGw0cynJUJ2iEQ3dks` (hoặc user cung cấp key mới)
- Quota: 10,000 units/day (free tier)
- Enable tại: https://console.cloud.google.com/apis/library/youtube.googleapis.com

**TikTok API v2**
- Client Key: `aw31du5c21khbh3g` (ví dụ, user sẽ cung cấp)
- Client Secret: `xigDd4P1hyYL7dg3Wg3XSuixsmPgKc2w` (ví dụ)
- OAuth 2.0 flow: Authorization Code
- Redirect URI: `http://localhost:8000/callback`
- Scopes: `user.info.basic,video.list,video.insights,comment.list`

---

## 3. CẤU TRÚC THƯ MỤC

```
tiktok_analytics/                    # Root directory
│
├── modules/                         # Core modules
│   ├── __init__.py                 # Exports: YouTubeScraper, TikTokScraper, SentimentAnalyzer, MetricsAnalyzer
│   ├── youtube_scraper.py          # YouTube Data API v3 implementation (284 lines)
│   ├── tiktok_scraper.py           # TikTok API v2 OAuth implementation (412 lines)
│   ├── sentiment_analyzer.py       # Vietnamese sentiment: PhoBERT + underthesea (489 lines)
│   └── metrics_analyzer.py         # Engagement metrics + visualizations (717 lines)
│
├── data/                           # Scraped raw data (JSON)
│   ├── youtube_<channel_id>.json
│   └── tiktok_<username>.json
│
├── reports/                        # Generated reports
│   ├── youtube_analysis/           # YouTube analysis output
│   │   ├── sentiment_analysis.png
│   │   ├── engagement_metrics.png
│   │   ├── trending_analysis.png
│   │   ├── correlation_matrix.png
│   │   ├── sentiment_interactive.html
│   │   ├── engagement_interactive.html
│   │   ├── metrics.csv
│   │   ├── sentiment.csv
│   │   └── report.txt
│   │
│   └── tiktok_analysis/            # TikTok analysis output
│       └── (same structure)
│
├── config.py                       # Configuration settings (44 lines)
├── requirements.txt                # Dependencies
├── .gitignore                      # Git ignore (includes .env, .env.tiktok)
├── .env                            # YouTube API key (not committed)
├── .env.tiktok                     # TikTok tokens (not committed)
│
├── demo_tvu.py                     # Demo: YouTube analysis (Trà Vinh University channel)
├── demo_tiktok.py                  # Demo: TikTok analysis
├── tiktok_oauth.py                 # OAuth 2.0 helper script (130 lines)
│
├── README.md                       # Documentation (YouTube focus)
├── TIKTOK_GUIDE.md                 # TikTok OAuth setup guide
└── PROJECT_BLUEPRINT.md            # This file
```

---

## 4. MODULE 1: YOUTUBE SCRAPER

### 4.1 File: `modules/youtube_scraper.py`

**Chức năng**: Thu thập dữ liệu từ YouTube sử dụng YouTube Data API v3

**Class**: `YouTubeScraper`

**Methods chính**:

```python
class YouTubeScraper:
    def __init__(self, api_key: str):
        """Khởi tạo với YouTube API key"""
        
    def get_channel_info(self, channel_id: str = None, channel_username: str = None) -> Dict:
        """
        Lấy thông tin channel (subscriber count, video count, view count)
        
        Returns:
            {
                'channel_id': str,
                'title': str,
                'description': str,
                'published_at': str,
                'thumbnail': str,
                'subscriber_count': int,
                'video_count': int,
                'view_count': int,
                'uploads_playlist_id': str
            }
        """
        
    def get_channel_videos(self, channel_id: str = None, channel_username: str = None, 
                          max_videos: int = 50) -> List[Dict]:
        """
        Lấy danh sách videos từ channel
        
        Returns: List of video dicts containing:
            {
                'video_id': str,
                'title': str,
                'description': str,
                'published_at': str,
                'thumbnail': str,
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'duration': str (ISO 8601),
                'tags': List[str]
            }
        """
        
    def get_video_comments(self, video_id: str, max_comments: int = 100) -> List[Dict]:
        """
        Lấy comments từ video
        
        Returns: List of comment dicts:
            {
                'comment_id': str,
                'author': str,
                'text': str,
                'like_count': int,
                'published_at': str,
                'reply_count': int
            }
        """
        
    def scrape_channel_data(self, channel_id: str = None, channel_username: str = None,
                           max_videos: int = 30, max_comments_per_video: int = 50) -> Dict:
        """
        MAIN METHOD: Thu thập toàn bộ dữ liệu channel
        
        Workflow:
        1. Get channel info
        2. Get videos list
        3. For each video: get comments
        4. Save to JSON file (data/youtube_<channel_id>.json)
        
        Returns:
            {
                'channel_info': Dict,
                'videos': List[Dict],
                'total_videos_scraped': int,
                'total_comments_scraped': int,
                'scraped_at': str (ISO timestamp)
            }
        """
```

**Quota Management**:
- `channels().list`: 1 unit
- `playlistItems().list`: 1 unit
- `videos().list`: 1 unit
- `commentThreads().list`: 1 unit
- Total for 30 videos + 50 comments each: ~1,600 units

**Error Handling**:
- `HttpError`: API quota exceeded, invalid key, video disabled comments
- `Exception`: Network errors, JSON parsing errors

---

## 5. MODULE 2: TIKTOK SCRAPER

### 5.1 File: `modules/tiktok_scraper.py`

**Chức năng**: Thu thập dữ liệu từ TikTok API v2 với OAuth 2.0

**Class**: `TikTokScraper`

**OAuth Flow**:

```
1. User clicks authorization URL
   → https://www.tiktok.com/v2/auth/authorize/?client_key=...&scope=...
   
2. User logs in TikTok, grants permissions
   → Redirected to: http://localhost:8000/callback?code=<AUTH_CODE>
   
3. Exchange code for access token
   → POST https://open.tiktokapis.com/v2/oauth/token/
   
4. Receive access token + refresh token
   → Save to .env.tiktok
   
5. Use access token for API calls
   → Authorization: Bearer <ACCESS_TOKEN>
```

**Methods chính**:

```python
class TikTokScraper:
    def __init__(self, client_key: str, client_secret: str, access_token: str = None):
        """Khởi tạo với TikTok credentials"""
        
    def get_authorization_url(self, redirect_uri: str, scope: str = None) -> str:
        """
        Tạo URL để user authorize
        
        Returns: Authorization URL
        """
        
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict:
        """
        Đổi authorization code → access token
        
        Returns:
            {
                'access_token': str,
                'refresh_token': str,
                'expires_in': int (seconds),
                'token_type': 'Bearer',
                'scope': str
            }
        """
        
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """Làm mới access token khi hết hạn"""
        
    def get_user_info(self) -> Dict:
        """
        Lấy thông tin user profile
        
        Returns:
            {
                'user_id': str,
                'username': str,
                'display_name': str,
                'avatar_url': str,
                'follower_count': int,
                'following_count': int,
                'likes_count': int,
                'video_count': int
            }
        """
        
    def get_user_videos(self, max_videos: int = 30, cursor: int = 0) -> Dict:
        """
        Lấy danh sách videos của user
        
        Returns:
            {
                'videos': List[Dict],
                'has_more': bool,
                'cursor': int
            }
        """
        
    def get_video_comments(self, video_id: str, max_comments: int = 50) -> List[Dict]:
        """Lấy comments từ video"""
        
    def scrape_user_profile(self, max_videos: int = 30, max_comments_per_video: int = 50) -> Dict:
        """
        MAIN METHOD: Thu thập toàn bộ dữ liệu user
        
        Similar to YouTubeScraper.scrape_channel_data()
        Save to: data/tiktok_<username>.json
        """
```

**API Endpoints**:
- `/v2/oauth/token/` - Token management
- `/v2/user/info/` - User profile
- `/v2/video/list/` - Video list
- `/v2/video/query/` - Video details
- `/v2/comment/list/` - Comments

---

## 6. MODULE 3: SENTIMENT ANALYZER

### 6.1 File: `modules/sentiment_analyzer.py`

**Chức năng**: Phân tích sentiment (cảm xúc) từ comments - **CHUYÊN cho tiếng Việt**

**Class**: `SentimentAnalyzer`

**Vietnamese Models**:

1. **underthesea** (Primary - Fast):
   - Accuracy: 70-75%
   - Speed: ~1000 texts/second
   - Installation: `pip install underthesea`
   - Usage: `underthesea.sentiment(text)` → 'positive', 'negative', 'neutral'

2. **PhoBERT** (Optional - High Accuracy):
   - Model: `wonrax/phobert-base-vietnamese-sentiment`
   - Accuracy: 85-90%
   - Speed: ~50 texts/second (CPU), ~200 texts/second (GPU)
   - Size: ~400MB download (first time only)
   - Returns: Probabilities for positive/negative/neutral

3. **VADER** (Fallback - English):
   - For English comments only
   - Compound score: -1 (negative) to +1 (positive)

**Methods chính**:

```python
class SentimentAnalyzer:
    def __init__(self, use_vietnamese: bool = True, use_transformers: bool = False):
        """
        Args:
            use_vietnamese: Use Vietnamese models (default: True)
            use_transformers: Use PhoBERT (slow but accurate) vs underthesea (fast)
        """
        
    def analyze_text(self, text: str) -> Dict:
        """
        Phân tích sentiment của 1 đoạn text
        
        Returns:
            {
                'sentiment': str,  # 'positive', 'negative', 'neutral'
                'score': float,    # -1 to 1 (or 0-1 depending on model)
                'confidence': float,  # 0-1
                'language': str,   # 'vi', 'en', etc.
                'model_used': str  # 'underthesea_vi', 'phobert', 'vader'
            }
        """
        
    def analyze_comments(self, comments: List[Dict]) -> Dict:
        """
        Phân tích sentiment của nhiều comments
        
        Args:
            comments: List of dicts with 'text' field
        
        Returns:
            {
                'total_comments': int,
                'positive_count': int,
                'negative_count': int,
                'neutral_count': int,
                'positive_percentage': float,
                'negative_percentage': float,
                'neutral_percentage': float,
                'average_score': float,
                'comments': List[Dict]  # Original comments + sentiment results
            }
        """
        
    def analyze_profile_sentiment(self, profile_data: Dict) -> Dict:
        """
        Phân tích sentiment cho toàn bộ profile (all videos' comments)
        
        Returns:
            {
                'overall_sentiment': str,
                'total_comments_analyzed': int,
                'sentiment_distribution': Dict,
                'videos_sentiment': List[Dict],  # Per-video sentiment
                'top_positive_comments': List[Dict],
                'top_negative_comments': List[Dict]
            }
        """
```

**Language Detection**:
- Uses `langdetect` library
- Auto-switch between Vietnamese and English models
- Fallback: Use VADER if language is not Vietnamese/English

**Text Preprocessing**:
```python
def clean_text(self, text: str) -> str:
    """
    Clean text before sentiment analysis
    - Remove URLs
    - Remove excessive punctuation
    - Remove emojis (or convert to text)
    - Lowercase
    - Remove extra whitespace
    """
```

---

## 7. MODULE 4: METRICS ANALYZER

### 7.1 File: `modules/metrics_analyzer.py`

**Chức năng**: Tính toán metrics + tạo visualizations + sinh báo cáo

**Class**: `MetricsAnalyzer`

**Metrics Calculations**:

```python
# 7 metrics chính:

1. engagement_rate = (likes + comments + shares) / views × 100
   → Tỷ lệ tương tác cơ bản

2. like_rate = likes / views × 100
   → Tỷ lệ người xem bấm like

3. comment_rate = comments / views × 100
   → Tỷ lệ người xem để lại comment

4. share_rate = shares / views × 100
   → Tỷ lệ chia sẻ (viral potential)

5. save_rate = saves / views × 100
   → Tỷ lệ lưu video (high-quality content indicator)

6. interaction_rate = (likes + comments + shares + saves) / views × 100
   → Tổng tất cả tương tác

7. virality_score = (shares × 10 + likes + comments × 2) / views
   → Điểm viral (shares được weight cao hơn)
```

**Methods chính**:

```python
class MetricsAnalyzer:
    def __init__(self):
        """Setup matplotlib style, seaborn palette"""
        
    def calculate_engagement_metrics(self, video_data: Dict) -> Dict:
        """
        Tính metrics cho 1 video
        
        Returns:
            {
                'video_id': str,
                'title': str,
                'views': int,
                'likes': int,
                'comments': int,
                'shares': int,
                'saves': int,
                'engagement_rate': float,
                'like_rate': float,
                'comment_rate': float,
                'share_rate': float,
                'save_rate': float,
                'interaction_rate': float,
                'virality_score': float
            }
        """
        
    def analyze_profile_metrics(self, profile_data: Dict) -> Dict:
        """
        Phân tích metrics cho toàn bộ profile
        
        Returns:
            {
                'total_videos': int,
                'total_views': int,
                'total_engagement': int,
                'average_engagement_rate': float,
                'average_virality_score': float,
                'top_videos_by_engagement': List[Dict],  # Top 10
                'top_videos_by_views': List[Dict],
                'top_videos_by_virality': List[Dict],
                'engagement_trend': Dict,  # Time-based analysis
                'metrics_summary': Dict
            }
        """
        
    def create_visualizations(self, metrics_data: Dict, sentiment_data: Dict, 
                            output_dir: str = 'reports/analysis') -> None:
        """
        Tạo 4 loại visualizations:
        
        1. sentiment_analysis.png + sentiment_interactive.html
           - Pie chart: Sentiment distribution
           - Bar chart: Sentiment count
        
        2. engagement_metrics.png + engagement_interactive.html
           - Top 10 videos by engagement rate
           - Bar chart showing engagement vs views
        
        3. trending_analysis.png
           - Line chart: Engagement trend over time
           - Shows if channel is growing/declining
        
        4. correlation_matrix.png
           - Heatmap: Correlation between metrics
           - Shows which metrics relate to each other
        """
        
    def generate_report(self, profile_data: Dict, metrics_data: Dict, 
                       sentiment_data: Dict, output_file: str = 'report.txt') -> str:
        """
        Sinh báo cáo text tổng hợp
        
        Sections:
        1. Channel/User Overview
        2. Engagement Metrics Summary
        3. Sentiment Analysis Results
        4. Top Performing Content
        5. Insights & Patterns
        6. Recommendations
        
        Returns: Report text (also saves to file)
        """
```

**Visualization Libraries**:
- **matplotlib + seaborn**: Static PNG charts (high-quality, publication-ready)
- **plotly**: Interactive HTML charts (hover, zoom, pan)

---

## 8. CONFIGURATION FILE

### 8.1 File: `config.py`

```python
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
```

---

## 9. DEMO SCRIPTS

### 9.1 File: `demo_tvu.py` (YouTube Demo)

**Mục đích**: Demo phân tích channel YouTube "Đại học Trà Vinh"

```python
"""
Demo: Phân tích YouTube channel Trà Vinh University
Channel: https://www.youtube.com/@DaiHocTraVinh
"""

from modules import YouTubeScraper, SentimentAnalyzer, MetricsAnalyzer
from dotenv import load_dotenv
import os

# Load API key from .env
load_dotenv()
api_key = os.getenv('YOUTUBE_API_KEY')

# Initialize
youtube = YouTubeScraper(api_key)
sentiment = SentimentAnalyzer(use_vietnamese=True, use_transformers=False)
metrics = MetricsAnalyzer()

# Channel info
CHANNEL_ID = "UCe3T-bJiSkDNLrgadyvBjRA"  # Trà Vinh University
print("🎬 Đang phân tích channel Trà Vinh University...")

# Step 1: Scrape data
print("\n📥 Bước 1: Thu thập dữ liệu...")
profile_data = youtube.scrape_channel_data(
    channel_id=CHANNEL_ID,
    max_videos=30,
    max_comments_per_video=50
)

# Step 2: Sentiment analysis
print("\n🧠 Bước 2: Phân tích sentiment...")
sentiment_data = sentiment.analyze_profile_sentiment(profile_data)

# Step 3: Calculate metrics
print("\n📊 Bước 3: Tính toán metrics...")
metrics_data = metrics.analyze_profile_metrics(profile_data)

# Step 4: Create visualizations
print("\n📈 Bước 4: Tạo visualizations...")
metrics.create_visualizations(
    metrics_data,
    sentiment_data,
    output_dir='reports/youtube_analysis'
)

# Step 5: Generate report
print("\n📝 Bước 5: Sinh báo cáo...")
report = metrics.generate_report(
    profile_data,
    metrics_data,
    sentiment_data,
    output_file='reports/youtube_analysis/report.txt'
)

print("\n✅ Hoàn thành!")
print(f"📁 Báo cáo tại: reports/youtube_analysis/")
```

### 9.2 File: `demo_tiktok.py` (TikTok Demo)

**Mục đích**: Demo phân tích TikTok user profile

```python
"""
Demo: Phân tích TikTok user profile
Yêu cầu: Đã chạy tiktok_oauth.py để lấy access token
"""

from modules import TikTokScraper, SentimentAnalyzer, MetricsAnalyzer
from dotenv import load_dotenv
import os

# Load credentials from .env.tiktok
load_dotenv('.env.tiktok')
client_key = os.getenv('TIKTOK_CLIENT_KEY')
client_secret = os.getenv('TIKTOK_CLIENT_SECRET')
access_token = os.getenv('TIKTOK_ACCESS_TOKEN')

# Initialize
tiktok = TikTokScraper(client_key, client_secret, access_token)
sentiment = SentimentAnalyzer(use_vietnamese=True, use_transformers=False)
metrics = MetricsAnalyzer()

print("🎵 Đang phân tích TikTok profile...")

# Step 1: Scrape data
print("\n📥 Bước 1: Thu thập dữ liệu...")
profile_data = tiktok.scrape_user_profile(
    max_videos=30,
    max_comments_per_video=50
)

# Transform TikTok data → common format
def transform_tiktok_to_common_format(data):
    """Convert TikTok data structure to match YouTube format"""
    # Implementation here...
    pass

profile_data = transform_tiktok_to_common_format(profile_data)

# Steps 2-5: Same as YouTube demo
# ...

print("\n✅ Hoàn thành!")
print(f"📁 Báo cáo tại: reports/tiktok_analysis/")
```

---

## 10. OAUTH HELPER

### 10.1 File: `tiktok_oauth.py`

**Mục đích**: Interactive script để lấy TikTok access token

```python
"""
TikTok OAuth 2.0 Helper
Interactive script để authorize và lấy access token

Usage:
    python tiktok_oauth.py
"""

from modules import TikTokScraper
import os

# Config
CLIENT_KEY = "aw31du5c21khbh3g"  # User sẽ thay bằng key của họ
CLIENT_SECRET = "xigDd4P1hyYL7dg3Wg3XSuixsmPgKc2w"
REDIRECT_URI = "http://localhost:8000/callback"

# Initialize
scraper = TikTokScraper(CLIENT_KEY, CLIENT_SECRET)

print("=" * 60)
print("🎵 TIKTOK OAUTH 2.0 AUTHORIZATION")
print("=" * 60)

# Step 1: Generate authorization URL
auth_url = scraper.get_authorization_url(
    redirect_uri=REDIRECT_URI,
    scope="user.info.basic,video.list,video.insights,comment.list"
)

print("\n📋 BƯỚC 1: AUTHORIZE TRÊN TIKTOK")
print("-" * 60)
print("Copy URL sau và mở trong trình duyệt:\n")
print(auth_url)
print()
print("Sau khi đăng nhập và cho phép, bạn sẽ được redirect đến:")
print("http://localhost:8000/callback?code=XXXXXXXXXXXX")
print()

# Step 2: Get authorization code from user
code = input("📥 Paste mã code từ URL (phần sau ?code=): ").strip()

if not code:
    print("❌ Không có code. Thoát.")
    exit(1)

# Step 3: Exchange code for token
print("\n🔄 Đang đổi code lấy access token...")
try:
    token_data = scraper.exchange_code_for_token(code, REDIRECT_URI)
    
    access_token = token_data['access_token']
    refresh_token = token_data['refresh_token']
    expires_in = token_data['expires_in']
    
    print("✅ Thành công!")
    print(f"   Access Token: {access_token[:20]}...")
    print(f"   Refresh Token: {refresh_token[:20]}...")
    print(f"   Expires in: {expires_in} seconds ({expires_in//3600} hours)")
    
    # Step 4: Save to .env.tiktok
    with open('.env.tiktok', 'w') as f:
        f.write(f"TIKTOK_CLIENT_KEY={CLIENT_KEY}\n")
        f.write(f"TIKTOK_CLIENT_SECRET={CLIENT_SECRET}\n")
        f.write(f"TIKTOK_ACCESS_TOKEN={access_token}\n")
        f.write(f"TIKTOK_REFRESH_TOKEN={refresh_token}\n")
    
    print("\n💾 Đã lưu credentials vào .env.tiktok")
    
    # Step 5: Test connection
    print("\n🧪 Đang test connection...")
    scraper.access_token = access_token
    scraper.headers["Authorization"] = f"Bearer {access_token}"
    
    user_info = scraper.get_user_info()
    print(f"✅ Connected! User: {user_info['display_name']}")
    print(f"   Followers: {user_info['follower_count']:,}")
    print(f"   Videos: {user_info['video_count']}")
    
except Exception as e:
    print(f"❌ Lỗi: {e}")
    exit(1)

print("\n" + "=" * 60)
print("🎉 HOÀN THÀNH! Giờ bạn có thể chạy:")
print("   python demo_tiktok.py")
print("=" * 60)
```

---

## 11. HƯỚNG DẪN TRIỂN KHAI

### 11.1 Bước 1: Setup Environment

```bash
# Clone hoặc tạo folder mới
mkdir tiktok_analytics
cd tiktok_analytics

# Tạo virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Cài dependencies
pip install -r requirements.txt

# Download NLTK data (cho VADER)
python -c "import nltk; nltk.download('vader_lexicon')"
```

### 11.2 Bước 2: Tạo cấu trúc thư mục

```bash
mkdir modules
mkdir data
mkdir reports
mkdir reports/youtube_analysis
mkdir reports/tiktok_analysis
```

### 11.3 Bước 3: Tạo các module files

Tạo các file theo thứ tự:

1. `config.py` - Copy từ section 8
2. `modules/__init__.py` - Export classes
3. `modules/youtube_scraper.py` - Section 4
4. `modules/tiktok_scraper.py` - Section 5
5. `modules/sentiment_analyzer.py` - Section 6
6. `modules/metrics_analyzer.py` - Section 7

### 11.4 Bước 4: Setup API credentials

**YouTube:**
```bash
# Tạo .env file
echo "YOUTUBE_API_KEY=AIzaSyClfAZjwp8JMSH86ZGw0cynJUJ2iEQ3dks" > .env
```

**TikTok:**
```bash
# Chạy OAuth helper
python tiktok_oauth.py
# Follow instructions to get access token
# File .env.tiktok sẽ được tạo tự động
```

### 11.5 Bước 5: Tạo demo scripts

1. `demo_tvu.py` - Section 9.1
2. `demo_tiktok.py` - Section 9.2
3. `tiktok_oauth.py` - Section 10

### 11.6 Bước 6: Test

```bash
# Test YouTube module
python demo_tvu.py

# Test TikTok module (sau khi OAuth)
python tiktok_oauth.py
python demo_tiktok.py
```

---

## 12. TESTING & VALIDATION

### 12.1 Test Cases

**YouTube Module:**
```python
# Test case 1: Valid channel ID
channel_id = "UCe3T-bJiSkDNLrgadyvBjRA"  # Trà Vinh University
data = youtube.scrape_channel_data(channel_id, max_videos=5)
assert data['total_videos_scraped'] > 0
assert 'videos' in data
assert 'channel_info' in data

# Test case 2: Invalid channel ID
data = youtube.scrape_channel_data("INVALID_ID")
assert data is None

# Test case 3: Quota exceeded
# Should raise HttpError 403
```

**Sentiment Module:**
```python
# Test Vietnamese text
text_vi = "Video này rất hay và bổ ích!"
result = sentiment.analyze_text(text_vi)
assert result['sentiment'] == 'positive'
assert result['language'] == 'vi'
assert result['model_used'] in ['underthesea_vi', 'phobert']

# Test English text
text_en = "This video is terrible and boring."
result = sentiment.analyze_text(text_en)
assert result['sentiment'] == 'negative'
assert result['language'] == 'en'
assert result['model_used'] == 'vader'
```

**Metrics Module:**
```python
# Test engagement calculation
video_data = {
    'views': 10000,
    'likes': 500,
    'comments': 100,
    'shares': 50
}
metrics_result = metrics.calculate_engagement_metrics(video_data)
expected_engagement = (500 + 100 + 50) / 10000 * 100  # 6.5%
assert abs(metrics_result['engagement_rate'] - expected_engagement) < 0.01
```

### 12.2 Expected Results (Demo TVU)

```
Channel: Đại học Trà Vinh
- Subscribers: ~6,300
- Total videos: ~815
- Videos scraped: 30
- Comments per video: ~50
- Total comments: ~1,500

Sentiment:
- Positive: ~70-75%
- Neutral: ~15-20%
- Negative: ~5-10%

Engagement rate: ~2-3% (typical for educational content)
Most active video: Usually university events, student activities
```

---

## 13. YÊU CẦU ĐẶC BIỆT

### 13.1 Vietnamese Sentiment - QUAN TRỌNG

**Tại sao cần Vietnamese models?**
- Vietnamese grammar khác English (SVO + tones + particles)
- VADER (English) chỉ đạt ~40-50% accuracy trên tiếng Việt
- PhoBERT/underthesea trained specifically trên Vietnamese corpus

**Model Selection:**

| Model | Accuracy | Speed | Size | Use case |
|-------|----------|-------|------|----------|
| underthesea | 70-75% | Fast (1000 texts/s) | ~50MB | Production, real-time |
| PhoBERT | 85-90% | Slow (50 texts/s CPU) | ~400MB | Research, high accuracy needed |
| VADER | 40-50% (VI) | Fast | ~1MB | English fallback only |

**Recommendation**: 
- Default: `use_vietnamese=True, use_transformers=False` (underthesea)
- High accuracy: `use_vietnamese=True, use_transformers=True` (PhoBERT)

### 13.2 API Quotas & Limits

**YouTube Data API v3:**
- Quota: 10,000 units/day (free tier)
- Example usage: 30 videos + 50 comments each = ~1,600 units
- Limit: ~6 full channel scrapes per day
- Workaround: Use multiple API keys or Google Cloud paid tier

**TikTok API v2:**
- Rate limit: 100 requests/day (free tier)
- Token expiry: 24 hours (need refresh token)
- Scope restrictions: Personal data only (can't access other users without permission)

### 13.3 Error Handling

**Must handle:**
1. API quota exceeded (YouTube 403 error)
2. Invalid/expired access token (TikTok 401 error)
3. Video with comments disabled (YouTube)
4. Network timeouts
5. JSON parsing errors
6. Missing fields in API response

**Best practices:**
```python
try:
    data = scraper.scrape_channel_data(channel_id)
except HttpError as e:
    if e.resp.status == 403:
        print("API quota exceeded")
    elif e.resp.status == 404:
        print("Channel not found")
except Exception as e:
    print(f"Unknown error: {e}")
```

### 13.4 Data Privacy

**Important:**
- Add `.env` and `.env.tiktok` to `.gitignore`
- NEVER commit API keys to Git
- Use environment variables for sensitive data
- TikTok tokens có thể access personal account → Cần bảo mật cao

**`.gitignore` must include:**
```
.env
.env.local
.env.tiktok
*.env
api_keys.txt
data/*.json
reports/
```

---

## 14. PHẦN MỞ RỘNG (OPTIONAL)

### 14.1 Additional Features (có thể thêm)

1. **Multi-account support**: Analyze multiple YouTube channels hoặc TikTok users
2. **Scheduling**: Auto-scrape daily/weekly với APScheduler
3. **Database**: Lưu dữ liệu vào PostgreSQL/MongoDB thay vì JSON
4. **Web UI**: Flask/FastAPI dashboard để visualize data
5. **Export formats**: PDF reports, Excel, PowerPoint slides
6. **Email notifications**: Send report tự động qua email
7. **Competitor analysis**: So sánh nhiều channels
8. **Keyword tracking**: Track specific hashtags/keywords

### 14.2 Performance Optimization

1. **Caching**: Cache API responses với Redis
2. **Async requests**: Use `asyncio` + `aiohttp` cho parallel API calls
3. **Batch processing**: Group videos/comments để reduce API calls
4. **GPU acceleration**: Use CUDA cho PhoBERT nếu có GPU

---

## 15. CHECKLIST HOÀN THÀNH

Khi triển khai xong, AI assistant cần verify:

- [ ] All 4 modules created và working
- [ ] YouTube scraper tested với valid channel ID
- [ ] TikTok OAuth flow completed
- [ ] Sentiment analyzer tested với Vietnamese text
- [ ] Metrics calculation accurate (manual check formulas)
- [ ] 4 visualizations generated successfully
- [ ] Report text file created với insights
- [ ] CSV exports working (metrics.csv, sentiment.csv)
- [ ] .gitignore includes sensitive files
- [ ] Dependencies installed without errors
- [ ] Demo scripts run end-to-end
- [ ] Error handling working (test with invalid inputs)

---

## 16. TROUBLESHOOTING

### Common Issues:

**1. "Module not found" error**
```bash
# Solution: Ensure virtual environment activated
.venv\Scripts\activate
pip install -r requirements.txt
```

**2. YouTube API quota exceeded**
```python
# Solution: Use multiple API keys or wait 24h
# Or implement caching to reduce API calls
```

**3. PhoBERT download fails**
```python
# Solution: Download manually
from transformers import AutoTokenizer, AutoModelForSequenceClassification
model = AutoModelForSequenceClassification.from_pretrained(
    "wonrax/phobert-base-vietnamese-sentiment",
    cache_dir="./models"  # Specify local dir
)
```

**4. TikTok token expired**
```python
# Solution: Use refresh token
new_token = scraper.refresh_access_token(refresh_token)
```

**5. underthesea accuracy low**
```python
# Solution: Switch to PhoBERT
sentiment = SentimentAnalyzer(use_vietnamese=True, use_transformers=True)
```

---

## 17. CONTACT & SUPPORT

**Nếu cần hỗ trợ thêm:**

1. Check documentation: README.md, TIKTOK_GUIDE.md
2. Review error messages carefully
3. Google/Stack Overflow for specific errors
4. TikTok Developer Docs: https://developers.tiktok.com/doc
5. YouTube API Docs: https://developers.google.com/youtube/v3

---

## 18. KẾT LUẬN

Document này chứa **TẤT CẢ** thông tin cần thiết để tái tạo lại dự án. AI assistant nên:

1. **Đọc kỹ từ đầu đến cuối** trước khi start
2. **Follow exact structure** như mô tả
3. **Implement từng module theo thứ tự**: config → scrapers → sentiment → metrics → demos
4. **Test từng bước** trước khi move to next step
5. **Copy formulas chính xác** (especially metrics calculations)
6. **Handle Vietnamese** properly (underthesea/PhoBERT setup)
7. **Verify quotas** and implement error handling
8. **Create complete file structure** including data/ and reports/ folders

**Timeline estimate**: 2-3 hours cho experienced AI assistant

**Final check**: Run demo_tvu.py end-to-end và verify all outputs generated correctly.

---

**Document version**: 1.0  
**Date**: March 3, 2026  
**Author**: YouTube & TikTok Analytics AI Project  
**Purpose**: Complete blueprint for project replication by Claude 4.6 or other AI assistants

---

# 🎉 GOOD LUCK WITH IMPLEMENTATION! 🚀
