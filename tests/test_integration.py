"""
Integration Tests for YouTube Analytics System
"""
import unittest
import os
import json
from pathlib import Path
from modules.youtube_scraper import scrape_youtube_channel
from modules.metrics_analyzer import MetricsAnalyzer
from modules.sentiment_analyzer import SentimentAnalyzer


class TestYouTubeIntegration(unittest.TestCase):
    """Integration tests cho YouTube Analytics pipeline"""
    
    @classmethod
    def setUpClass(cls):
        """Setup môi trường test"""
        cls.api_key = os.environ.get('YOUTUBE_API_KEY')
        if not cls.api_key:
            raise unittest.SkipTest("YOUTUBE_API_KEY not set")
        
        # Test với channel có ít videos
        cls.test_channel = "UCaxnllxL894OHbc_6VQcGmA"  # TVU
    
    def test_full_pipeline(self):
        """Test toàn bộ pipeline từ scrape → metrics → sentiment"""
        
        # Step 1: Scrape data
        data = scrape_youtube_channel(
            api_key=self.api_key,
            channel_id=self.test_channel,
            max_videos=5,
            max_comments=10
        )
        
        self.assertIsNotNone(data)
        self.assertIn('videos', data)
        self.assertGreater(len(data['videos']), 0)
        
        # Step 2: Calculate metrics
        metrics_analyzer = MetricsAnalyzer()
        
        for video in data['videos']:
            metrics = metrics_analyzer.calculate_engagement_metrics(video)
            self.assertIn('engagement_rate', metrics)
            self.assertGreaterEqual(metrics['engagement_rate'], 0.0)
        
        # Step 3: Analyze sentiment
        sentiment_analyzer = SentimentAnalyzer()
        
        for video in data['videos']:
            if 'comments' in video and video['comments']:
                for comment in video['comments'][:5]:  # Test first 5
                    result = sentiment_analyzer.analyze_text(comment['text'])
                    self.assertIn('final_sentiment', result)


class TestDataPersistence(unittest.TestCase):
    """Test lưu và đọc dữ liệu"""
    
    def test_save_and_load_json(self):
        """Test lưu và đọc file JSON"""
        from utils import DataManager
        
        manager = DataManager()
        
        test_data = {
            'username': '@test_user',
            'videos': [
                {'id': '123', 'stats': {'viewCount': 1000}}
            ]
        }
        
        # Save
        filepath, timestamp = manager.get_save_path('youtube', 'test_channel', 'test', 'json')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        # Load
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data['username'], test_data['username'])
        
        # Cleanup
        if filepath.exists():
            os.remove(filepath)


if __name__ == '__main__':
    unittest.main()
