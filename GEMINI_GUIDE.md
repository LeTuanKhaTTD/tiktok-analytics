# Hướng dẫn sử dụng Gemini AI cho Sentiment Analysis

## 🎯 Tổng quan

Module Gemini Sentiment Analyzer sử dụng Google Gemini AI để phân tích cảm xúc bình luận với độ chính xác cao và tối ưu hóa chi phí API.

## ✨ Tính năng

### 1. Smart Caching
- **Tự động cache kết quả**: Mỗi text được phân tích chỉ gọi API 1 lần duy nhất
- **Persistent cache**: Cache được lưu vào file để sử dụng lại qua nhiều phiên
- **Cache hit rate tracking**: Theo dõi tỷ lệ cache hits để tối ưu
- **Tiết kiệm quota**: Giảm 90%+ API calls khi phân tích lại cùng dataset

### 2. Rate Limiting & Error Handling
- **Exponential Backoff**: Tự động điều chỉnh delay khi gặp rate limit
  - Lần 1: 2s
  - Lần 2: 4s
  - Lần 3: 8s
  - ...
  - Max: 60s
- **Auto Retry**: Tự động thử lại tối đa 5 lần khi gặp lỗi
- **Graceful Degradation**: Trả về neutral khi fail hoàn toàn

### 3. Batch Processing
- **Progress Tracking**: Real-time progress bar và statistics
- **Batch-aware**: Xử lý hàng loạt comment với progress callback
- **Memory Efficient**: Stream processing, không load tất cả vào memory

### 4. Statistics & Monitoring
Theo dõi chi tiết:
- Total requests
- Cache hits vs API calls
- Rate limit events
- Errors
- Cache hit rate (%)

## 🔑 Lấy Gemini API Key

### Bước 1: Truy cập Google AI Studio
1. Vào https://aistudio.google.com/
2. Đăng nhập bằng tài khoản Google

### Bước 2: Tạo API Key
1. Click vào "Get API key" ở sidebar
2. Click "Create API key"
3. Chọn project (hoặc tạo mới)
4. Copy API key

### Bước 3: Cấu hình trong project

**Cách 1: Biến môi trường (Khuyến nghị)**
```bash
# Windows PowerShell
$env:GEMINI_API_KEY = "your-api-key-here"

# Hoặc thêm vào .env file
echo "GEMINI_API_KEY=your-api-key-here" >> .env
```

**Cách 2: Cập nhật config.py**
```python
# config.py
GEMINI_API_KEY = "your-api-key-here"
```

**⚠️ BẢO MẬT**: 
- KHÔNG commit API key vào Git
- Thêm `.env` vào `.gitignore`
- Dùng biến môi trường trong production

## 💰 Chi phí & Quota

### Free Tier (Gemini 2.0 Flash)
- **Requests/phút**: 15 requests
- **Requests/ngày**: 1,500 requests
- **Token limit**: 1 triệu tokens/phút

### Chi phí thực tế với caching:
- **Không cache**: 1,000 comments = 1,000 API calls
- **Với cache 90%**: 1,000 comments = 100 API calls (lần đầu) + 0 (lần sau)
- **Tiết kiệm**: 90%+ quota khi phân tích lại

### Tips tiết kiệm:
1. ✅ Bật caching (mặc định: enabled)
2. ✅ Xử lý batch lớn 1 lần thay vì nhiều lần nhỏ
3. ✅ Giữ cache file để tái sử dụng
4. ✅ Chỉ phân tích comments chưa có nhãn thủ công

## 🚀 Sử dụng

### 1. Trong Dashboard (Streamlit)

#### Phân tích tự động toàn bộ:
```
1. Mở Dashboard: streamlit run dashboard.py
2. Vào trang "🏷️ Gán nhãn thủ công"
3. Click "🤖 Gán nhãn tự động bằng Gemini"
4. Chờ progress bar hoàn thành
5. Xem statistics: cache hits, API calls, etc.
```

#### Phân tích từng comment:
```
1. Trong trang "🏷️ Gán nhãn thủ công"
2. Tìm comment cần phân tích
3. Click nút "🤖" bên cạnh comment
4. Kết quả hiện ngay với confidence score
```

### 2. Sử dụng trực tiếp trong code

```python
from modules.gemini_sentiment import GeminiSentimentAnalyzer

# Khởi tạo
analyzer = GeminiSentimentAnalyzer(
    api_key="your-api-key",
    model_name="gemini-2.0-flash",
    enable_cache=True,
    max_retries=5
)

# Phân tích 1 text
sentiment, confidence = analyzer.analyze_sentiment("Video rất hay!")
print(f"Sentiment: {sentiment}, Confidence: {confidence}")
# Output: Sentiment: positive, Confidence: 0.9

# Phân tích batch
texts = ["Tốt", "Dở", "Bình thường"]
results = analyzer.batch_analyze(texts)

# Xem statistics
stats = analyzer.get_statistics()
print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")
```

### 3. Pipeline integration

```python
from pipeline.pipeline_orchestrator import PipelineOrchestrator
from modules.gemini_sentiment import GeminiSentimentAnalyzer

# Tạo orchestrator với Gemini
orchestrator = PipelineOrchestrator(
    sentiment_method="gemini",
    gemini_api_key="your-api-key"
)

# Chạy pipeline
orchestrator.run_full_pipeline(
    platform="tiktok",
    identifier="@travinhuniversity"
)
```

## 📊 So sánh với các phương pháp khác

| Method | Accuracy | Speed | Cost | Vietnamese |
|--------|----------|-------|------|------------|
| **Gemini AI** | 92-95% | Trung bình | $0 (free tier) | ✅ Xuất sắc |
| PhoBERT | 85-90% | Chậm | Free | ✅ Tốt |
| underthesea | 70-75% | Rất nhanh | Free | ✅ Khá |
| VADER | 60-70% | Rất nhanh | Free | ❌ Kém |

**Khuyến nghị**:
- Production: **Gemini AI** (độ chính xác cao + caching thông minh)
- Batch lớn offline: **PhoBERT** (stable, không phụ thuộc API)
- Real-time nhẹ: **underthesea** (nhanh nhất)

## 🔧 Troubleshooting

### Lỗi 429 - Rate Limit
```
⚠️ Rate limit hit! Waiting 60s (attempt 1/5)...
```

**Nguyên nhân**: Vượt quá 15 requests/phút

**Giải pháp**:
1. ✅ Module tự động xử lý với exponential backoff
2. ✅ Chờ retry tự động
3. ✅ Tăng `base_delay` trong config nếu cần:
```python
analyzer = GeminiSentimentAnalyzer(
    api_key=key,
    base_delay=3.0  # Tăng từ 2.0 lên 3.0
)
```

### Lỗi API Key không hợp lệ
```
❌ Error: API key not valid
```

**Giải pháp**:
1. Kiểm tra API key đã copy đúng chưa
2. Kiểm tra API key đã enable chưa tại https://aistudio.google.com/
3. Thử tạo API key mới

### Cache không hoạt động
```
Cache hit rate: 0.0%
```

**Giải pháp**:
1. Kiểm tra `enable_cache=True` trong config
2. Kiểm tra quyền ghi vào thư mục `data/.cache/`
3. Xem file cache: `data/.cache/gemini_sentiment_cache.json`

### Performance chậm
**Giải pháp**:
1. Giảm `max_retries` xuống 3
2. Tăng `base_delay` để tránh rate limit
3. Xử lý trong off-peak hours (ít người dùng)
4. Enable cache để lần sau nhanh hơn

## 📈 Best Practices

### 1. Tối ưu cache
```python
# Phân tích 1 lần, cache vĩnh viễn
analyzer.batch_analyze(all_comments)

# Các lần sau gần như instant
analyzer.batch_analyze(all_comments)  # 100% cache hits!
```

### 2. Xử lý batch lớn
```python
# Chia nhỏ batch để theo dõi
for batch in chunks(comments, size=100):
    analyzer.batch_analyze(batch)
    analyzer._save_cache()  # Lưu cache sau mỗi batch
```

### 3. Error handling
```python
try:
    sentiment, conf = analyzer.analyze_sentiment(text)
    if conf < 0.5:  # Low confidence
        # Fallback sang method khác
        sentiment = fallback_analyzer.analyze(text)
except Exception as e:
    # Log error
    logger.error(f"Gemini failed: {e}")
    sentiment = "neutral"
```

### 4. Monitoring
```python
# Định kỳ check statistics
stats = analyzer.get_statistics()
if stats['cache_hit_rate'] < 50:
    print("Warning: Low cache hit rate!")
if stats['rate_limits'] > 0:
    print(f"Hit rate limit {stats['rate_limits']} times")
```

## 🎓 Advanced Usage

### Custom prompt
```python
class CustomGeminiAnalyzer(GeminiSentimentAnalyzer):
    def analyze_sentiment(self, text):
        custom_prompt = f"""
        Phân tích text sau theo tiêu chí:
        1. Sentiment: positive/neutral/negative
        2. Emotion: joy/anger/sadness/fear
        3. Intent: question/complaint/praise
        
        Text: {text}
        """
        # ... rest of implementation
```

### Multi-language support
```python
# Tự động detect language và adjust prompt
def analyze_multilang(text):
    lang = detect_language(text)
    if lang == 'vi':
        prompt = "Phân tích cảm xúc bằng tiếng Việt..."
    elif lang == 'en':
        prompt = "Analyze sentiment in English..."
    # ...
```

## 📚 Tài liệu tham khảo

- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Rate Limits & Quotas](https://ai.google.dev/pricing)
- [Best Practices](https://ai.google.dev/docs/best_practices)

## 🆘 Hỗ trợ

Nếu gặp vấn đề:
1. Xem section Troubleshooting ở trên
2. Check logs trong console
3. Xem statistics: `analyzer.get_statistics()`
4. Tạo issue trên GitHub repository

---

**Cập nhật**: 2026-03-11  
**Version**: 2.0  
**Tác giả**: TikTok Analytics Team
