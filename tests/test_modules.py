"""
Unit Tests for Sentiment Analyzer Module
"""
import unittest
from modules.sentiment_analyzer import SentimentAnalyzer


class TestSentimentAnalyzer(unittest.TestCase):
    """Test cases cho Sentiment Analyzer"""
    
    @classmethod
    def setUpClass(cls):
        """Khởi tạo analyzer một lần cho tất cả tests"""
        cls.analyzer = SentimentAnalyzer(use_vietnamese=True, use_transformers=False)
    
    def test_clean_text(self):
        """Test làm sạch text"""
        text = "Check this out! http://example.com @user #hashtag"
        cleaned = self.analyzer.clean_text(text)
        
        self.assertNotIn('http://', cleaned)
        self.assertNotIn('@user', cleaned)
        self.assertIn('hashtag', cleaned)  # Hash removed, text kept
    
    def test_positive_sentiment_vietnamese(self):
        """Test phân tích sentiment tích cực tiếng Việt"""
        texts = [
            "Trường này đẹp quá!",
            "Tuyệt vời, rất hay",
            "Tôi yêu trường này"
        ]
        
        for text in texts:
            result = self.analyzer.analyze_text(text)
            self.assertIn(result['final_sentiment'], ['positive', 'neutral'])
            self.assertGreater(result['confidence'], 0.0)
    
    def test_negative_sentiment_vietnamese(self):
        """Test phân tích sentiment tiêu cực tiếng Việt"""
        texts = [
            "Dở quá, không hay",
            "Tệ lắm",
            "Không thích"
        ]
        
        for text in texts:
            result = self.analyzer.analyze_text(text)
            self.assertIn(result['final_sentiment'], ['negative', 'neutral'])
    
    def test_empty_text(self):
        """Test xử lý text rỗng"""
        result = self.analyzer.analyze_text("")
        self.assertEqual(result['final_sentiment'], 'neutral')
        self.assertEqual(result['confidence'], 0.5)
    
    def test_english_text_fallback(self):
        """Test fallback sang VADER cho tiếng Anh"""
        text = "This is amazing! I love it!"
        result = self.analyzer.analyze_text(text)
        
        self.assertIn(result['final_sentiment'], ['positive', 'negative', 'neutral'])
        self.assertGreater(result['confidence'], 0.0)
    
    def test_mixed_language(self):
        """Test xử lý mixed language"""
        text = "This video rất hay! Tôi like it"
        result = self.analyzer.analyze_text(text)
        
        # Should still work and return a sentiment
        self.assertIsNotNone(result['final_sentiment'])
    
    def test_batch_analysis(self):
        """Test phân tích nhiều texts"""
        texts = [
            "Tuyệt vời quá!",
            "Bình thường thôi",
            "Không hay lắm"
        ]
        
        for text in texts:
            result = self.analyzer.analyze_text(text)
            self.assertIn('final_sentiment', result)
            self.assertIn('confidence', result)
            self.assertIn('method', result)


class TestMetricsAnalyzer(unittest.TestCase):
    """Test cases cho Metrics Analyzer"""
    
    def test_engagement_rate_calculation(self):
        """Test tính engagement rate"""
        from modules.metrics_analyzer import MetricsAnalyzer
        
        analyzer = MetricsAnalyzer()
        
        video_data = {
            'video_id': 'test123',
            'stats': {
                'viewCount': 1000,
                'likeCount': 100,
                'commentCount': 50,
                'favoriteCount': 0
            }
        }
        
        metrics = analyzer.calculate_engagement_metrics(video_data)
        
        # Engagement = (100 + 50) / 1000 * 100 = 15%
        self.assertEqual(metrics['engagement_rate'], 15.0)
    
    def test_zero_views_handling(self):
        """Test xử lý video có 0 views"""
        from modules.metrics_analyzer import MetricsAnalyzer
        
        analyzer = MetricsAnalyzer()
        
        video_data = {
            'video_id': 'test456',
            'stats': {
                'viewCount': 0,
                'likeCount': 0,
                'commentCount': 0,
                'favoriteCount': 0
            }
        }
        
        metrics = analyzer.calculate_engagement_metrics(video_data)
        
        # Should not crash, return 0.0
        self.assertEqual(metrics['engagement_rate'], 0.0)


if __name__ == '__main__':
    unittest.main()
