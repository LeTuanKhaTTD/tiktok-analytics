# YouTube Analytics AI Module 📺

Module AI phân tích tương tác và cảm xúc người dùng trên YouTube. Thu thập và phân tích dữ liệu từ các video YouTube bao gồm views, likes, comments và phân tích sentiment từ comments để hiểu được cảm nhận của người xem.

## ✨ Tính năng

### 📊 Thu thập dữ liệu
- Thu thập thông tin channel và video từ YouTube Data API v3
- Lấy các metrics: views, likes, comments, favorites
- Thu thập comments từ mỗi video
- Lưu trữ metadata: tags, category, duration, thời gian đăng

### 😊 Phân tích Sentiment (Tiếng Việt)
- Phân tích cảm xúc từ comments (positive, negative, neutral)
- **Gemini AI** - Độ chính xác cao nhất 92-95% với caching thông minh (khuyến nghị) 🆕
- **PhoBERT** - Chính xác cao 85-90% (offline, stable)
- **underthesea** - Nhanh, 70-75% accuracy (lightweight)
- **VADER** - Fallback cho tiếng Anh
- Tự động phát hiện ngôn ngữ và chọn model phù hợp

### 📈 Phân tích Metrics
- **Engagement Rate**: (likes + comments) / views × 100%
- **Like Rate, Comment Rate**
- **Virality Score**: Đánh giá khả năng lan truyền
- **Interaction Rate**: Tất cả các tương tác
- Phân tích xu hướng theo thời gian
- So sánh performance giữa các video

### 📉 Visualization
- Biểu đồ phân phối engagement rates
- Biểu đồ sentiment analysis (pie charts)
- Timeline performance
- So sánh top performing videos
- Xuất báo cáo dạng text và hình ảnh

## 🔑 Lấy YouTube API Key

### Bước 1: Truy cập Google Cloud Console
1. Vào https://console.cloud.google.com/
2. Đăng nhập bằng tài khoản Google

### Bước 2: Tạo Project mới
1. Click vào dropdown project ở góc trên
2. Click "New Project"
3. Đặt tên project (ví dụ: "YouTube Analytics")
4. Click "Create"

### Bước 3: Enable YouTube Data API v3
1. Vào mục "APIs & Services" > "Library"
2. Tìm "YouTube Data API v3"
3. Click vào và nhấn "Enable"

### Bước 4: Tạo API Key
1. Vào "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API Key"
3. Copy API key được tạo ra
4. (Khuyến nghị) Click "Restrict Key" để bảo mật:
   - API restrictions: Chọn "YouTube Data API v3"
   - Application restrictions: Chọn phù hợp với app của bạn

### Quota và Giới hạn
- **FREE tier**: 10,000 units/day
- **Chi phí**: 
  - Search: 100 units per request
  - Videos.list: 1 unit per request
  - Comments: 1 unit per request
- **Ví dụ**: Phân tích 30 videos với 50 comments mỗi video ~ 80-100 units

## 🚀 Cài đặt

### Yêu cầu hệ thống
- Python 3.8 trở lên
- Windows/Linux/MacOS
- YouTube Data API key

### Bước 1: Clone hoặc tải project
```bash
cd youtube_analytics
```

### Bước 2: Tạo môi trường ảo (khuyến nghị)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/MacOS
source venv/bin/activate
```

### Bước 3: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Bước 4: Cấu hình API Key
Có 2 cách:

**Cách 1: Biến môi trường (khuyến nghị)**
```bash
# Windows (PowerShell)
$env:YOUTUBE_API_KEY="YOUR_API_KEY_HERE"

# Linux/MacOS
export YOUTUBE_API_KEY="YOUR_API_KEY_HERE"
```

**Cách 2: File .env**
```bash
# Tạo file .env
echo "YOUTUBE_API_KEY=YOUR_API_KEY_HERE" > .env
```

## 📖 Sử dụng

### Demo nhanh - Kênh Đại học Trà Vinh
```bash
python demo_tvu.py
```

### Phân tích channel bất kỳ
```bash
# Dùng Channel ID
python main.py UCaxnllxL894OHbc_6VQcGmA -v 30 -c 50

# Dùng username
python main.py @username -v 30 -c 50
```

### Tham số:
- **identifier**: Channel ID (UC...) hoặc @username (bắt buộc)
- `-k, --api-key`: YouTube API key (hoặc dùng biến môi trường)
- `-v, --videos`: Số lượng video phân tích (mặc định: 30)
- `-c, --comments`: Số comments mỗi video (mặc định: 50)
- `--no-sentiment`: Bỏ qua phân tích sentiment
- `--no-visualizations`: Bỏ qua tạo biểu đồ
- `--use-transformers`: Dùng PhoBERT (chậm, chính xác cao)
- `-o, --output`: Thư mục lưu dữ liệu (mặc định: data)
- `-r, --reports`: Thư mục lưu báo cáo (mặc định: reports)

### Ví dụ chi tiết:

**1. Phân tích nhanh (10 videos, 20 comments)**
```bash
python main.py UCaxnllxL894OHbc_6VQcGmA -v 10 -c 20
```

**2. Phân tích đầy đủ (50 videos, 100 comments)**
```bash
python main.py UCaxnllxL894OHbc_6VQcGmA -v 50 -c 100
```

**3. Dùng PhoBERT cho độ chính xác cao**
```bash
python main.py UCaxnllxL894OHbc_6VQcGmA --use-transformers
```

**4. Chỉ phân tích metrics (không sentiment)**
```bash
python main.py UCaxnllxL894OHbc_6VQcGmA --no-sentiment
```

## 📁 Cấu trúc Project

```
youtube_analytics/
├── modules/
│   ├── __init__.py
│   ├── youtube_scraper.py       # Thu thập dữ liệu YouTube
│   ├── sentiment_analyzer.py    # Phân tích sentiment (PhoBERT, underthesea, VADER)
│   └── metrics_analyzer.py      # Phân tích metrics và visualization
├── data/                         # Dữ liệu raw
├── reports/                      # Báo cáo và biểu đồ
├── main.py                       # Entry point chính
├── demo_tvu.py                   # Demo nhanh
├── demo_tvu_full.py              # Demo đầy đủ
├── test_api.py                   # Test API key
├── test_vietnamese_sentiment.py  # Test sentiment tiếng Việt
├── config.py                     # Cấu hình
├── requirements.txt              # Dependencies
├── .env.example                  # Template cho .env
└── README.md
```

## 📊 Output

### 1. Báo cáo text (.txt)
```
==================================================================================
                    YOUTUBE ANALYTICS REPORT
==================================================================================

👤 PROFILE INFORMATION
Username: Trường Đại học Trà Vinh
Total Videos Analyzed: 30
Analysis Date: 2026-03-03 10:30:00

📊 OVERALL ENGAGEMENT METRICS
Average Engagement Rate: 3.45%
Average Like Rate: 2.89%
Average Comment Rate: 0.56%
Virality Score: 0.0234

😊 SENTIMENT ANALYSIS
Total Comments Analyzed: 1,234
Positive: 68.2%
Negative: 5.3%
Neutral: 26.5%

🎯 KEY INSIGHTS
• Tỷ lệ engagement cao hơn trung bình kênh giáo dục (>3%)
• Sentiment tích cực mạnh, cộng đồng hài lòng
• Video gần đây có xu hướng tăng tương tác
...
```

### 2. Biểu đồ (.png)
- `engagement_overview.png` - Tổng quan engagement
- `sentiment_distribution.png` - Phân bố sentiment
- `engagement_timeline.png` - Xu hướng theo thời gian
- `top_videos.png` - Top video performance

### 3. Dữ liệu (.json, .csv)
- Raw data từ YouTube API
- Kết quả phân tích sentiment chi tiết
- Metrics cho từng video

## 🧩 Modules

### 1. YouTubeScraper (`youtube_scraper.py`)
Thu thập dữ liệu từ YouTube Data API v3:
- Channel info (title, subscribers, total videos/views)
- Video list với metadata
- Comments từ mỗi video

**Example:**
```python
from modules.youtube_scraper import YouTubeScraper

scraper = YouTubeScraper(api_key="YOUR_API_KEY")
data = scraper.scrape_channel(
    channel_id="UCaxnllxL894OHbc_6VQcGmA",
    max_videos=30,
    max_comments=50
)
```

### 2. SentimentAnalyzer (`sentiment_analyzer.py`)
Phân tích sentiment với nhiều model:
- **underthesea** - Chuyên tiếng Việt, nhanh (1000+ comments/s)
- **PhoBERT** - Chính xác cao 85-90% (chậm hơn)
- **VADER** - Fallback cho tiếng Anh

**Example:**
```python
from modules.sentiment_analyzer import SentimentAnalyzer

# Khuyến nghị: dùng underthesea (nhanh, đủ tốt)
analyzer = SentimentAnalyzer(use_vietnamese=True, use_transformers=False)

# Hoặc dùng PhoBERT (chậm, chính xác cao)
analyzer = SentimentAnalyzer(use_vietnamese=True, use_transformers=True)

result = analyzer.analyze_text("Video rất hay!")
# → {'final_sentiment': 'positive', 'confidence': 0.85}
```

### 3. MetricsAnalyzer (`metrics_analyzer.py`)
Phân tích metrics và tạo visualization:
- Tính toán 7 engagement metrics
- Phân tích xu hướng
- Tạo biểu đồ
- Generate báo cáo

**Example:**
```python
from modules.metrics_analyzer import MetricsAnalyzer

analyzer = MetricsAnalyzer()
metrics = analyzer.analyze_profile_metrics(profile_data)
report = analyzer.generate_report(profile_data, metrics, sentiment_data)
```

## 🔧 Cấu hình (config.py)

```python
# Sentiment Analysis
USE_VIETNAMESE = True    # Dùng model tiếng Việt
USE_TRANSFORMERS = False  # False: underthesea (nhanh), True: PhoBERT (chính xác)

# Scraping
DEFAULT_VIDEO_COUNT = 30
DEFAULT_COMMENTS_PER_VIDEO = 50

# Metrics thresholds
ENGAGEMENT_THRESHOLD_HIGH = 5.0  # %
ENGAGEMENT_THRESHOLD_LOW = 2.0   # %

# Output
GENERATE_VISUALIZATIONS = True
EXPORT_CSV = True
```

## ❓ FAQ

### YouTube API không hoạt động?
1. Kiểm tra API key đã enable YouTube Data API v3 chưa
2. Kiểm tra quota còn lại (10,000 units/day)
3. Kiểm tra API restrictions
4. Test bằng: `python test_api.py`

### Sentiment analysis kém chính xác?
- Mặc định dùng **underthesea** (70-75% accuracy cho tiếng Việt)
- Nâng cao: dùng **PhoBERT** với `--use-transformers` (85-90%)
- VADER chỉ tốt cho tiếng Anh

### Làm sao tăng tốc độ?
- Dùng underthesea (không dùng PhoBERT) → nhanh gấp 50-100 lần
- Giảm số videos (`-v`) và comments (`-c`)
- Bỏ visualization nếu không cần: `--no-visualizations`

### Hết quota YouTube API?
- Free tier: 10,000 units/day
- Giảm số videos và comments
- Đợi 24h để quota reset
- Hoặc mua thêm quota (paid tier)

## 📦 Dependencies chính

- **google-api-python-client** - YouTube Data API
- **underthesea** - Sentiment tiếng Việt (nhanh)
- **transformers** - PhoBERT (chính xác cao)
- **vaderSentiment** - Sentiment tiếng Anh
- **matplotlib, seaborn** - Visualization
- **pandas, numpy** - Data processing

## 📝 License

MIT License - Sử dụng cho mục đích học tập và nghiên cứu. Tuân thủ Terms of Service của YouTube.

## 🤝 Đóng góp

Contributions, issues và feature requests đều welcome!

## 📧 Liên hệ

- Issues: GitHub Issues
- Email: [your-email]

---

**Made with ❤️ for YouTube Analytics**

