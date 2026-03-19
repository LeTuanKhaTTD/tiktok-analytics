"""
Test script cho Gemini Sentiment Analyzer
Chạy script này để kiểm tra Gemini API hoạt động đúng

Usage:
    python test_gemini.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.gemini_sentiment import GeminiSentimentAnalyzer
from config import GEMINI_API_KEY


def test_single_analysis():
    """Test phân tích 1 comment"""
    print("\n" + "="*70)
    print("TEST 1: Phân tích đơn lẻ")
    print("="*70)
    
    # Lấy API key
    api_key = GEMINI_API_KEY or os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ Chưa cấu hình GEMINI_API_KEY!")
        print("\nCách cấu hình:")
        print("  1. Lấy key: https://aistudio.google.com/")
        print("  2. Set biến môi trường:")
        print("     Windows: $env:GEMINI_API_KEY = 'your-key'")
        print("     Linux: export GEMINI_API_KEY='your-key'")
        print("  3. Hoặc cập nhật config.py")
        return False
    
    # Khởi tạo analyzer
    print(f"\n🔧 Khởi tạo GeminiSentimentAnalyzer...")
    analyzer = GeminiSentimentAnalyzer(
        api_key=api_key,
        enable_cache=True,
        max_retries=3,
        base_delay=1.0
    )
    
    # Test cases
    test_cases = [
        "Video này rất hay và bổ ích, cảm ơn admin!",
        "Dở quá, không xem được",
        "OK, bình thường thôi",
        "👍👍👍 Tuyệt vời",
        "Không hiểu gì cả 😢"
    ]
    
    print(f"\n🧪 Test với {len(test_cases)} comments...\n")
    
    for i, text in enumerate(test_cases, 1):
        print(f"{i}. Text: {text}")
        sentiment, confidence = analyzer.analyze_sentiment(text)
        
        emoji = {"positive": "✅", "neutral": "⚪", "negative": "❌"}
        print(f"   → {emoji.get(sentiment, '❓')} Sentiment: {sentiment}")
        print(f"   → Confidence: {confidence:.2f}\n")
    
    # Statistics
    stats = analyzer.get_statistics()
    print("="*70)
    print("📊 STATISTICS")
    print("="*70)
    print(f"Total requests:  {stats['total_requests']}")
    print(f"API calls:       {stats['api_calls']}")
    print(f"Cache hits:      {stats['cache_hits']}")
    print(f"Cache hit rate:  {stats['cache_hit_rate']:.1f}%")
    print(f"Rate limits:     {stats['rate_limits']}")
    print(f"Errors:          {stats['errors']}")
    
    return True


def test_batch_analysis():
    """Test phân tích batch"""
    print("\n" + "="*70)
    print("TEST 2: Phân tích batch")
    print("="*70)
    
    api_key = GEMINI_API_KEY or os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ Chưa cấu hình GEMINI_API_KEY!")
        return False
    
    analyzer = GeminiSentimentAnalyzer(api_key=api_key)
    
    # Test batch
    texts = [
        "Hay quá!",
        "Dở",
        "OK",
        "Tuyệt vời lắm",
        "Không thích",
        "Bình thường",
        "Rất tốt",
        "Tệ quá",
        "Được",
        "Xuất sắc!"
    ]
    
    print(f"\n🧪 Test batch với {len(texts)} comments...\n")
    
    def progress_callback(current, total, message):
        print(f"Progress: {current}/{total} - {message}")
    
    results = analyzer.batch_analyze(texts, progress_callback=progress_callback)
    
    # Show results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    for result in results:
        sentiment_counts[result["sentiment"]] += 1
    
    print(f"✅ Positive: {sentiment_counts['positive']}")
    print(f"⚪ Neutral:  {sentiment_counts['neutral']}")
    print(f"❌ Negative: {sentiment_counts['negative']}")
    
    # Statistics
    stats = analyzer.get_statistics()
    print("\n" + "="*70)
    print("📊 STATISTICS")
    print("="*70)
    print(f"Total requests:  {stats['total_requests']}")
    print(f"API calls:       {stats['api_calls']}")
    print(f"Cache hits:      {stats['cache_hits']}")
    print(f"Cache hit rate:  {stats['cache_hit_rate']:.1f}%")
    
    return True


def test_cache():
    """Test cache functionality"""
    print("\n" + "="*70)
    print("TEST 3: Cache functionality")
    print("="*70)
    
    api_key = GEMINI_API_KEY or os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ Chưa cấu hình GEMINI_API_KEY!")
        return False
    
    analyzer = GeminiSentimentAnalyzer(api_key=api_key, enable_cache=True)
    
    text = "Test cache: Video này rất hay!"
    
    print(f"\n🧪 Test cache với text: '{text}'\n")
    
    # Lần 1 - should call API
    print("1️⃣  Lần 1 (should call API)...")
    sentiment1, conf1 = analyzer.analyze_sentiment(text)
    stats1 = analyzer.get_statistics()
    print(f"   Result: {sentiment1} ({conf1:.2f})")
    print(f"   API calls: {stats1['api_calls']}, Cache hits: {stats1['cache_hits']}")
    
    # Lần 2 - should use cache
    print("\n2️⃣  Lần 2 (should use cache)...")
    sentiment2, conf2 = analyzer.analyze_sentiment(text)
    stats2 = analyzer.get_statistics()
    print(f"   Result: {sentiment2} ({conf2:.2f})")
    print(f"   API calls: {stats2['api_calls']}, Cache hits: {stats2['cache_hits']}")
    
    # Verify
    if stats2['cache_hits'] > stats1['cache_hits']:
        print("\n✅ Cache working correctly!")
    else:
        print("\n⚠️  Cache might not be working")
    
    return True


def main():
    """Main test function"""
    print("\n" + "="*70)
    print("🧪 GEMINI SENTIMENT ANALYZER TEST SUITE")
    print("="*70)
    print("Testing Gemini AI integration for sentiment analysis")
    print("Version: 2.0 | Date: 2026-03-11")
    
    try:
        # Run tests
        test1_ok = test_single_analysis()
        if not test1_ok:
            return
        
        input("\n⏸️  Press Enter to continue to batch test...")
        test2_ok = test_batch_analysis()
        
        input("\n⏸️  Press Enter to continue to cache test...")
        test3_ok = test_cache()
        
        # Summary
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED")
        print("="*70)
        print("\n💡 Next steps:")
        print("  1. Chạy dashboard: streamlit run dashboard.py")
        print("  2. Vào trang 'Gán nhãn thủ công'")
        print("  3. Click 'Gán nhãn tự động bằng Gemini'")
        print("\n📚 Đọc thêm: GEMINI_GUIDE.md")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
