# ⚡ HƯỚNG DẪN SETUP NHANH - CÁC CẢI TIẾN MỚI

**Cập nhật:** 5 tháng 3, 2026  
**Thời gian:** ~10 phút

---

## 🎯 MỤC TIÊU

Setup nhanh các tính năng mới đã được thêm vào hệ thống:
- ✅ Testing framework
- ✅ Caching system
- ✅ Dashboard
- ✅ Logging
- ✅ Database
- ✅ REST API

---

## 📋 BƯỚC 1: CÀI ĐẶT DEPENDENCIES

```bash
# Activate virtual environment (nếu chưa)
cd d:\Thuc_tap\tiktok_analytics
.venv-2\Scripts\activate  # Windows

# Install tất cả dependencies mới
pip install -r requirements.txt

# Hoặc cài riêng từng nhóm:
pip install pytest pytest-cov pytest-mock
pip install fastapi uvicorn[standard] sqlalchemy
pip install streamlit
pip install redis
```

**Thời gian:** ~2-3 phút

---

## 📋 BƯỚC 2: SETUP ENVIRONMENT VARIABLES

```bash
# Copy template
cp .env.example .env

# Edit .env file
notepad .env  # Windows
# hoặc
nano .env     # Linux/Mac
```

**Nội dung .env:**
```bash
# YouTube API
YOUTUBE_API_KEY=YOUR_ACTUAL_API_KEY_HERE

# TikTok API (optional)
TIKTOK_CLIENT_KEY=your_tiktok_key_here
TIKTOK_CLIENT_SECRET=your_tiktok_secret_here

# Analysis Settings
DEFAULT_VIDEO_COUNT=30
DEFAULT_COMMENTS_PER_VIDEO=50
USE_VIETNAMESE=True
USE_TRANSFORMERS=False

# Output
OUTPUT_DIR=data
REPORTS_DIR=reports
```

⚠️ **LƯU Ý:** Thay `YOUR_ACTUAL_API_KEY_HERE` bằng YouTube API key thật của bạn!

**Thời gian:** ~1 phút

---

## 📋 BƯỚC 3: CHẠY TESTS

```bash
# Run all tests
pytest tests/ -v

# Với coverage report
pytest tests/ --cov=modules --cov-report=html

# Xem coverage report
start htmlcov\index.html  # Windows
```

**Kết quả mong đợi:**
```
tests/test_modules.py::TestSentimentAnalyzer::test_clean_text PASSED
tests/test_modules.py::TestSentimentAnalyzer::test_positive_sentiment_vietnamese PASSED
tests/test_modules.py::TestSentimentAnalyzer::test_negative_sentiment_vietnamese PASSED
...
==================== 10 passed in 15.23s ====================
```

**Thời gian:** ~15-20 giây

---

## 📋 BƯỚC 4: KHỞI TẠO DATABASE

```bash
# Chạy script khởi tạo database
python -c "from database.models import DatabaseManager; db = DatabaseManager(); print('Database initialized!')"
```

**Output:**
```
Database initialized!
```

**File được tạo:** `analytics.db` (SQLite database)

**Thời gian:** ~1 giây

---

## 📋 BƯỚC 5: TEST DASHBOARD

```bash
# Start Streamlit dashboard
streamlit run dashboard_app.py

# Mở browser tự động: http://localhost:8501
```

**Nếu chưa có data:**
1. Chạy một analysis trước:
   ```bash
   python main.py UCaxnllxL894OHbc_6VQcGmA --videos 10 --comments 20
   ```
2. Refresh dashboard

**Thời gian:** ~5 giây startup

---

## 📋 BƯỚC 6: TEST REST API

**Terminal 1 - Start API server:**
```bash
uvicorn api_server:app --reload --port 8000
```

**Terminal 2 - Test endpoints:**
```bash
# Health check
curl http://localhost:8000/health

# Start analysis (background task)
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d "{\"channel_id\": \"UCaxnllxL894OHbc_6VQcGmA\", \"max_videos\": 5}"

# Xem API docs (Swagger UI)
start http://localhost:8000/docs  # Windows
```

**Thời gian:** ~3 giây startup

---

## 📋 BƯỚC 7: TEST CACHING

```python
# Chạy trong Python console
from utils.cache_manager import SentimentCache
from modules.sentiment_analyzer import SentimentAnalyzer

cache = SentimentCache()
analyzer = SentimentAnalyzer()

# First run (miss)
import time
text = "Trường này đẹp quá!"

start = time.time()
result1 = cache.get(text)
if not result1:
    result1 = analyzer.analyze_text(text)
    cache.set(text, result1)
print(f"First run: {time.time() - start:.3f}s")

# Second run (hit)
start = time.time()
result2 = cache.get(text)
print(f"Second run: {time.time() - start:.3f}s")

# Stats
print(cache.get_stats())
```

**Output mong đợi:**
```
First run: 0.850s  (cache miss)
Second run: 0.002s (cache hit) 🚀
{'hits': 1, 'misses': 1, 'hit_rate': 50.0}
```

**Thời gian:** ~1 phút

---

## 📋 BƯỚC 8: TEST LOGGING

```python
# Chạy trong Python console
from utils.logger import AnalyticsLogger, monitor_performance
import time

logger = AnalyticsLogger(name="test_logger")

# Test log levels
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")

# Test decorator
@monitor_performance(logger)
def slow_function():
    time.sleep(0.5)
    return "Done"

result = slow_function()

# Check log file
# Xem: logs/test_logger.log
```

**Output:**
```
[2026-03-05 14:30:15] INFO     [test_logger] Info message
[2026-03-05 14:30:16] WARNING  [test_logger] Warning message
[2026-03-05 14:30:17] ERROR    [test_logger] Error message
[2026-03-05 14:30:18] INFO     [test_logger] slow_function completed in 0.50s
```

**Thời gian:** ~30 giây

---

## 🎉 HOÀN TẤT!

### ✅ Checklist

- [x] Dependencies installed
- [x] Environment variables configured
- [x] Tests passing
- [x] Database initialized
- [x] Dashboard working
- [x] API server running
- [x] Caching working
- [x] Logging working

### 🚀 Bước tiếp theo

1. **Chạy phân tích thật:**
   ```bash
   python main.py UCaxnllxL894OHbc_6VQcGmA --videos 30 --comments 50
   ```

2. **Xem kết quả trên Dashboard:**
   ```bash
   streamlit run dashboard_app.py
   ```

3. **Integrate với API:**
   ```bash
   # Start API
   uvicorn api_server:app --host 0.0.0.0 --port 8000
   
   # Call from other services
   curl http://localhost:8000/api/analyze -d '{"channel_id": "UCxxx"}'
   ```

4. **Deploy lên production:**
   ```bash
   # Build Docker
   docker build -t youtube-analytics .
   
   # Run container
   docker-compose up -d
   ```

---

## 🔧 TROUBLESHOOTING

### Lỗi: "ModuleNotFoundError: No module named 'xxx'"

**Giải pháp:**
```bash
pip install -r requirements.txt --upgrade
```

### Lỗi: "YOUTUBE_API_KEY not set"

**Giải pháp:**
1. Check file `.env` tồn tại
2. Check API key đã điền đúng
3. Restart terminal/IDE

### Lỗi: "Port 8000 already in use"

**Giải pháp:**
```bash
# Kill process trên port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9

# Hoặc dùng port khác:
uvicorn api_server:app --port 8001
```

### Tests fail với "Connection refused"

**Giải pháp:**
- Không cần API key cho unit tests
- Integration tests cần `YOUTUBE_API_KEY` trong `.env`
- Skip integration tests: `pytest tests/test_modules.py`

### Dashboard không hiển thị data

**Giải pháp:**
1. Chạy ít nhất 1 analysis trước
2. Check folder `data/` có files JSON không
3. Refresh browser (Ctrl+F5)

---

## 📚 TÀI LIỆU LIÊN QUAN

- [IMPROVEMENT_REPORT.md](IMPROVEMENT_REPORT.md) - Báo cáo chi tiết
- [README.md](README.md) - Hướng dẫn đầy đủ
- [QUICK_START.md](QUICK_START.md) - Hướng dẫn cơ bản

---

## 💬 HỖ TRỢ

**Nếu gặp vấn đề:**
1. Check logs trong `logs/` folder
2. Run với debug mode: `python main.py --debug`
3. Xem error messages chi tiết
4. Open GitHub Issue

---

**Chúc mừng! Bạn đã setup thành công! 🎉**
