"""
Gemini Sentiment Analyzer - Sử dụng Google Gemini AI để phân tích sentiment
Tối ưu hóa với caching, rate limiting, và error handling

Features:
- Smart caching để tránh gọi lại API
- Exponential backoff cho rate limiting
- Batch processing với progress tracking
- Fallback sang các method khác nếu Gemini fail
- Detailed logging và statistics
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from google import genai
from google.genai import types


class GeminiSentimentAnalyzer:
    """Phân tích sentiment sử dụng Google Gemini AI"""
    
    def __init__(self, 
                 api_key: str,
                 model_name: str = "gemini-2.0-flash",
                 cache_dir: str = "data/.cache",
                 enable_cache: bool = True,
                 max_retries: int = 5,
                 base_delay: float = 2.0):
        """
        Khởi tạo Gemini Sentiment Analyzer
        
        Args:
            api_key: Google Gemini API key
            model_name: Tên model Gemini (mặc định: gemini-2.0-flash)
            cache_dir: Thư mục cache kết quả
            enable_cache: Bật/tắt caching
            max_retries: Số lần retry tối đa khi gặp lỗi
            base_delay: Delay cơ bản giữa các request (giây)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.enable_cache = enable_cache
        
        # Khởi tạo Gemini client (google-genai SDK mới)
        self.client = genai.Client(api_key=api_key)
        
        # Setup cache
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "gemini_sentiment_cache.json"
        self.cache = self._load_cache()
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "errors": 0,
            "rate_limits": 0
        }
        
        print(f"✅ GeminiSentimentAnalyzer initialized")
        print(f"   Model: {model_name}")
        print(f"   Cache: {'enabled' if enable_cache else 'disabled'}")
    
    def _load_cache(self) -> Dict:
        """Tải cache từ file"""
        if not self.enable_cache:
            return {}
        
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Cannot load cache: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Lưu cache vào file"""
        if not self.enable_cache:
            return
        
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Cannot save cache: {e}")
    
    def _get_cache_key(self, text: str) -> str:
        """Tạo cache key từ text"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _get_cached_result(self, text: str) -> Optional[Tuple[str, float]]:
        """Lấy kết quả từ cache nếu có"""
        if not self.enable_cache:
            return None
        
        cache_key = self._get_cache_key(text)
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            result = self.cache[cache_key]
            return result["sentiment"], result["confidence"]
        return None
    
    def _cache_result(self, text: str, sentiment: str, confidence: float):
        """Lưu kết quả vào cache"""
        if not self.enable_cache:
            return
        
        cache_key = self._get_cache_key(text)
        self.cache[cache_key] = {
            "sentiment": sentiment,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_sentiment(self, text: str, save_cache_interval: int = 10) -> Tuple[str, float]:
        """
        Phân tích sentiment của một đoạn text
        
        Args:
            text: Text cần phân tích
            save_cache_interval: Lưu cache sau mỗi N requests
            
        Returns:
            Tuple (sentiment, confidence) với sentiment là 'positive', 'neutral', hoặc 'negative'
        """
        self.stats["total_requests"] += 1
        
        # Kiểm tra cache trước
        cached = self._get_cached_result(text)
        if cached:
            return cached
        
        # Gọi API với retry và exponential backoff
        for attempt in range(self.max_retries):
            try:
                # Tạo prompt
                prompt = (
                    "Phân tích cảm xúc (sentiment) của bình luận sau bằng tiếng Việt.\n"
                    "Trả về CHÍNH XÁC 1 trong 3 từ sau: positive, neutral, negative\n"
                    "Không giải thích, chỉ trả về 1 từ.\n\n"
                    f"Bình luận: {text}\n\nKết quả:"
                )
                
                # Gọi API (google-genai SDK mới)
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                result = response.text.strip().lower()
                
                # Parse kết quả
                sentiment = "neutral"
                confidence = 0.8
                
                if "positive" in result:
                    sentiment = "positive"
                    confidence = 0.9
                elif "negative" in result:
                    sentiment = "negative"
                    confidence = 0.9
                elif "neutral" in result:
                    sentiment = "neutral"
                    confidence = 0.85
                
                # Cập nhật stats
                self.stats["api_calls"] += 1
                
                # Cache kết quả
                self._cache_result(text, sentiment, confidence)
                
                # Lưu cache định kỳ
                if self.stats["api_calls"] % save_cache_interval == 0:
                    self._save_cache()
                
                # Delay giữa các request
                time.sleep(self.base_delay)
                
                return sentiment, confidence
                
            except Exception as e:
                error_str = str(e)
                
                # Xử lý rate limit (429 error)
                if "429" in error_str or "quota" in error_str.lower():
                    self.stats["rate_limits"] += 1
                    
                    # Tìm retry delay từ error message
                    wait_time = self._calculate_backoff(attempt)
                    
                    print(f"⚠️  Rate limit hit! Waiting {wait_time}s (attempt {attempt+1}/{self.max_retries})...")
                    time.sleep(wait_time)
                    continue
                
                # Các lỗi khác
                else:
                    self.stats["errors"] += 1
                    print(f"❌ Error: {e}")
                    
                    if attempt < self.max_retries - 1:
                        wait_time = self._calculate_backoff(attempt)
                        print(f"   Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        # Fallback về neutral với confidence thấp
                        return "neutral", 0.0
        
        # Nếu hết retry vẫn fail
        print(f"❌ Failed after {self.max_retries} retries. Returning neutral.")
        return "neutral", 0.0
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Tính thời gian chờ với exponential backoff"""
        # Exponential backoff: 2, 4, 8, 16, 32 seconds...
        wait_time = min(self.base_delay * (2 ** attempt), 60)  # Max 60s
        return wait_time
    
    def batch_analyze(self, 
                     texts: List[str],
                     progress_callback=None) -> List[Dict[str, any]]:
        """
        Phân tích sentiment cho nhiều text
        
        Args:
            texts: List các text cần phân tích
            progress_callback: Callback function nhận (current, total, message)
            
        Returns:
            List các dict chứa sentiment và confidence
        """
        results = []
        total = len(texts)
        
        print(f"\n🚀 Batch analyzing {total} texts...")
        print(f"   Cache size: {len(self.cache)} entries")
        
        for i, text in enumerate(texts):
            sentiment, confidence = self.analyze_sentiment(text)
            
            results.append({
                "text": text,
                "sentiment": sentiment,
                "confidence": confidence,
                "method": "gemini"
            })
            
            # Callback progress
            if progress_callback:
                progress_callback(i + 1, total, f"Analyzed {i+1}/{total}")
            
            # Log progress
            if (i + 1) % 10 == 0 or i == total - 1:
                cache_rate = (self.stats["cache_hits"] / self.stats["total_requests"] * 100) if self.stats["total_requests"] > 0 else 0
                print(f"   Progress: {i+1}/{total} | Cache hit rate: {cache_rate:.1f}%")
        
        # Lưu cache cuối cùng
        self._save_cache()
        
        return results
    
    def get_statistics(self) -> Dict:
        """Lấy thống kê sử dụng"""
        cache_hit_rate = (self.stats["cache_hits"] / self.stats["total_requests"] * 100) if self.stats["total_requests"] > 0 else 0
        
        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self.cache)
        }
    
    def clear_cache(self):
        """Xóa cache"""
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        print("✅ Cache cleared")
    
    def export_cache(self, output_path: str):
        """Xuất cache ra file khác"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
        print(f"✅ Cache exported to {output_path}")


# Singleton instance cho dashboard
_gemini_analyzer_instance = None

def get_gemini_analyzer(api_key: str = None) -> GeminiSentimentAnalyzer:
    """Lấy singleton instance của GeminiSentimentAnalyzer"""
    global _gemini_analyzer_instance
    
    if _gemini_analyzer_instance is None and api_key:
        _gemini_analyzer_instance = GeminiSentimentAnalyzer(api_key)
    
    return _gemini_analyzer_instance
