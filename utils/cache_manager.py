"""
Caching Layer for Sentiment Analysis
Giảm thời gian phân tích bằng cache kết quả đã xử lý
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta


class SentimentCache:
    """Cache cho sentiment analysis results"""
    
    def __init__(self, cache_dir: str = "cache", ttl_days: int = 30):
        """
        Args:
            cache_dir: Thư mục lưu cache
            ttl_days: Thời gian sống của cache (ngày)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(days=ttl_days)
        
        # Stats
        self.hits = 0
        self.misses = 0
    
    def _get_cache_key(self, text: str) -> str:
        """Tạo cache key từ text"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Lấy path của cache file"""
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, text: str) -> Optional[Dict]:
        """
        Lấy kết quả từ cache
        
        Returns:
            Dict với sentiment result hoặc None nếu không có/hết hạn
        """
        cache_key = self._get_cache_key(text)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            self.misses += 1
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            # Check expiration
            cached_time = datetime.fromisoformat(cached['cached_at'])
            if datetime.now() - cached_time > self.ttl:
                cache_path.unlink()  # Delete expired
                self.misses += 1
                return None
            
            self.hits += 1
            return cached['result']
            
        except Exception:
            self.misses += 1
            return None
    
    def set(self, text: str, result: Dict):
        """Lưu kết quả vào cache"""
        cache_key = self._get_cache_key(text)
        cache_path = self._get_cache_path(cache_key)
        
        cached_data = {
            'text': text[:100],  # Chỉ lưu 100 ký tự đầu để debug
            'result': result,
            'cached_at': datetime.now().isoformat()
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not cache result: {e}")
    
    def clear(self):
        """Xóa toàn bộ cache"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict:
        """Lấy thống kê cache"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': total,
            'hit_rate': round(hit_rate, 2)
        }


# ===== BATCH PROCESSING =====

def batch_analyze_sentiments(texts: list, analyzer, batch_size: int = 32) -> list:
    """
    Phân tích sentiment theo batch để tăng tốc
    
    Args:
        texts: List các text cần phân tích
        analyzer: SentimentAnalyzer instance
        batch_size: Kích thước mỗi batch
    
    Returns:
        List các kết quả sentiment
    """
    results = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        
        for text in batch:
            result = analyzer.analyze_text(text)
            results.append(result)
    
    return results


# ===== PARALLEL PROCESSING =====

def parallel_analyze_sentiments(texts: list, analyzer, num_workers: int = 4) -> list:
    """
    Phân tích sentiment song song với multiprocessing
    
    Args:
        texts: List các text cần phân tích
        analyzer: SentimentAnalyzer instance
        num_workers: Số workers song song
    
    Returns:
        List các kết quả sentiment
    """
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(analyzer.analyze_text, texts))
    
    return results


# ===== EXAMPLE USAGE =====

if __name__ == '__main__':
    from modules.sentiment_analyzer import SentimentAnalyzer
    
    # Khởi tạo với cache
    cache = SentimentCache()
    analyzer = SentimentAnalyzer()
    
    texts = [
        "Trường này đẹp quá!",
        "Tuyệt vời",
        "Trường này đẹp quá!",  # Duplicate - sẽ hit cache
    ]
    
    results = []
    for text in texts:
        # Try cache first
        cached_result = cache.get(text)
        
        if cached_result:
            results.append(cached_result)
        else:
            result = analyzer.analyze_text(text)
            cache.set(text, result)
            results.append(result)
    
    print("Results:", results)
    print("Cache stats:", cache.get_stats())
