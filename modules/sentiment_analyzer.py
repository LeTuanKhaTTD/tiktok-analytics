"""
Module phân tích sentiment (cảm xúc) từ comments và descriptions
Sử dụng PhoBERT - Model chuyên cho tiếng Việt
"""

from typing import List, Dict, Optional
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from langdetect import detect, LangDetectException
import re

# Try to import transformers and torch
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    import torch.nn.functional as F
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("  transformers/torch not available or incompatible version")

# Vietnamese NLP
try:
    from underthesea import sentiment as underthesea_sentiment
    UNDERTHESEA_AVAILABLE = True
except ImportError:
    UNDERTHESEA_AVAILABLE = False
    print("  underthesea not available. Install: pip install underthesea")


# Phân tích cảm xúc từ text (description, comments)
class SentimentAnalyzer:
    def __init__(self, use_vietnamese: bool = True, use_transformers: bool = False):
        """Khởi tạo Sentiment Analyzer với model tiếng Việt
        
        Args:
            use_vietnamese: Dùng model chuyên cho tiếng Việt (PhoBERT hoặc underthesea)
            use_transformers: Dùng PhoBERT transformer model (chính xác cao nhưng chậm)
        """
        self.vader = SentimentIntensityAnalyzer()  # Backup cho tiếng Anh
        self.use_vietnamese = use_vietnamese
        self.use_transformers = use_transformers
        
        # Vietnamese models
        self.phobert_model = None
        self.phobert_tokenizer = None
        
        if use_vietnamese and use_transformers:
            if not TRANSFORMERS_AVAILABLE:
                print("  Transformers/PyTorch không khả dụng hoặc version không tương thích")
                print(" Cần PyTorch >= 2.4 và transformers >= 4.36")
                if UNDERTHESEA_AVAILABLE:
                    print("→ Chuyển sang dùng underthesea (nhẹ hơn, 70-75% accuracy)")
                    self.use_transformers = False
                else:
                    print("→ Chuyển sang dùng VADER (cho tiếng Anh)")
                    self.use_vietnamese = False
                    self.use_transformers = False
            else:
                try:
                    print("🇻🇳 Đang tải PhoBERT - Model sentiment tiếng Việt...")
                    print("   (Lần đầu sẽ tải ~400MB, các lần sau dùng cache)")
                    
                    # PhoBERT fine-tuned cho sentiment tiếng Việt
                    model_name = "wonrax/phobert-base-vietnamese-sentiment"
                    
                    self.phobert_tokenizer = AutoTokenizer.from_pretrained(model_name)
                    self.phobert_model = AutoModelForSequenceClassification.from_pretrained(model_name)
                    
                    # Chuyển sang eval mode
                    self.phobert_model.eval()
                    
                    # Di chuyển sang GPU nếu có
                    if torch.cuda.is_available():
                        self.phobert_model = self.phobert_model.cuda()
                        print("    Đã tải model lên GPU")
                    else:
                        print("    Đã tải model (CPU mode)")
                        
                    print(" PhoBERT sẵn sàng (85-90% độ chính xác cho tiếng Việt)")
                    
                except Exception as e:
                    print(f" Không thể tải PhoBERT: {e}")
                    if UNDERTHESEA_AVAILABLE:
                        print("→ Chuyển sang dùng underthesea (nhẹ hơn, 70-75% accuracy)")
                        self.use_transformers = False
                    else:
                        print("→ Chuyển sang dùng VADER (cho tiếng Anh)")
                        self.use_vietnamese = False
                        self.use_transformers = False
        elif use_vietnamese and UNDERTHESEA_AVAILABLE:
            print(" Sử dụng underthesea cho sentiment tiếng Việt (nhanh, 70-75% accuracy)")
        elif use_vietnamese and not UNDERTHESEA_AVAILABLE:
            print("  underthesea chưa cài. Cài bằng: pip install underthesea")
            print("→ Sẽ dùng VADER (tối ưu cho tiếng Anh)")
            self.use_vietnamese = False
    
    def clean_text(self, text: str) -> str:
        """Làm sạch text"""
        if not text:
            return ""
        
        # Xóa URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        # Xóa mentions
        text = re.sub(r'@\w+', '', text)
        # Xóa hashtags nhưng giữ nội dung
        text = re.sub(r'#(\w+)', r'\1', text)
        # Xóa ký tự đặc biệt thừa
        text = re.sub(r'[^\w\s\u0080-\uFFFF]', ' ', text)
        # Xóa khoảng trắng thừa
        text = ' '.join(text.split())
        
        return text.strip()
    
    def detect_language(self, text: str) -> str:
        """Phát hiện ngôn ngữ của text"""
        try:
            return detect(text)
        except LangDetectException:
            return 'unknown'
    
    def analyze_vietnamese_phobert(self, text: str) -> Dict:
        """Phân tích sentiment bằng PhoBERT - Chuyên cho tiếng Việt
        
        Độ chính xác: 85-90% cho tiếng Việt
        Model: wonrax/phobert-base-vietnamese-sentiment
        """
        if not self.phobert_model or not self.phobert_tokenizer:
            return None
        
        try:
            # Tokenize
            inputs = self.phobert_tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=256,
                padding=True
            )
            
            # Di chuyển sang GPU nếu model ở GPU
            if next(self.phobert_model.parameters()).is_cuda:
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Predict
            with torch.no_grad():
                outputs = self.phobert_model(**inputs)
                probabilities = F.softmax(outputs.logits, dim=1)[0]
            
            # Labels: [NEG, NEU, POS]
            labels = ['negative', 'neutral', 'positive']
            predictions = probabilities.cpu().numpy()
            
            sentiment_idx = predictions.argmax()
            sentiment = labels[sentiment_idx]
            confidence = float(predictions[sentiment_idx])
            
            return {
                'method': 'phobert_vi',
                'sentiment': sentiment,
                'confidence': confidence,
                'probabilities': {
                    'negative': float(predictions[0]),
                    'neutral': float(predictions[1]),
                    'positive': float(predictions[2])
                }
            }
            
        except Exception as e:
            print(f"  PhoBERT error: {e}")
            return None
    
    def analyze_vietnamese_underthesea(self, text: str) -> Dict:
        """Phân tích sentiment bằng underthesea - Nhẹ, nhanh cho tiếng Việt
        
        Độ chính xác: 70-75% cho tiếng Việt
        Tốc độ: Rất nhanh (1000+ texts/giây)
        """
        if not UNDERTHESEA_AVAILABLE:
            return None
        
        try:
            # underthesea trả về: 'positive', 'negative', hoặc 'neutral'
            result = underthesea_sentiment(text)
            
            # Map confidence dựa trên độ dài và đặc điểm text
            # (underthesea không trả về confidence score)
            confidence = 0.7  # Default confidence
            
            return {
                'method': 'underthesea_vi',
                'sentiment': result.lower(),
                'confidence': confidence
            }
            
        except Exception as e:
            print(f"  underthesea error: {e}")
            return None
    
    def analyze_vader(self, text: str) -> Dict:
        """Phân tích sentiment bằng VADER - Tối ưu cho tiếng Anh
        
        Lưu ý: VADER không tốt cho tiếng Việt (accuracy ~50-60%)
        Chỉ dùng khi không có Vietnamese model
        """
        scores = self.vader.polarity_scores(text)
        
        # Phân loại
        compound = scores['compound']
        if compound >= 0.05:
            sentiment = 'positive'
        elif compound <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'method': 'vader',
            'sentiment': sentiment,
            'scores': scores,
            'confidence': abs(compound)
        }
    
    def analyze_text(self, text: str, methods: List[str] = None) -> Dict:
        """
        Phân tích sentiment của một đoạn text
        
        Args:
            text: Text cần phân tích
            methods: List các phương pháp ['phobert_vi', 'underthesea_vi', 'vader']
                    Nếu None sẽ tự động chọn phương pháp tốt nhất dựa trên ngôn ngữ
        
        Returns:
            Dictionary chứa kết quả phân tích
        """
        if not text or len(text.strip()) < 2:
            return {
                'text': text,
                'cleaned_text': '',
                'language': 'unknown',
                'results': {},
                'final_sentiment': 'neutral',
                'confidence': 0.0
            }
        
        # Làm sạch text
        cleaned = self.clean_text(text)
        if not cleaned:
            return {
                'text': text,
                'cleaned_text': '',
                'language': 'unknown',
                'results': {},
                'final_sentiment': 'neutral',
                'confidence': 0.0
            }
        
        # Phát hiện ngôn ngữ
        language = self.detect_language(cleaned)
        
        # Phân tích với các phương pháp khác nhau
        results = {}
        
        if methods is None:
            # Tự động chọn phương pháp tốt nhất dựa trên ngôn ngữ
            if language == 'vi' and self.use_vietnamese:
                # Tiếng Việt: Ưu tiên PhoBERT > underthesea > VADER
                if self.use_transformers and self.phobert_model:
                    methods = ['phobert_vi']
                elif UNDERTHESEA_AVAILABLE:
                    methods = ['underthesea_vi', 'vader']  # Voting 2 methods
                else:
                    methods = ['vader']
            else:
                # Tiếng Anh hoặc ngôn ngữ khác: Chỉ VADER
                methods = ['vader']
        
        # Phân tích với Vietnamese models
        if 'phobert_vi' in methods:
            phobert_result = self.analyze_vietnamese_phobert(cleaned)
            if phobert_result:
                results['phobert_vi'] = phobert_result
        
        if 'underthesea_vi' in methods:
            underthesea_result = self.analyze_vietnamese_underthesea(cleaned)
            if underthesea_result:
                results['underthesea_vi'] = underthesea_result
        
        # Fallback to VADER
        if 'vader' in methods:
            results['vader'] = self.analyze_vader(cleaned)
        
        # Tổng hợp kết quả
        final_sentiment, confidence = self._aggregate_results(results)
        
        return {
            'text': text,
            'cleaned_text': cleaned,
            'language': language,
            'results': results,
            'final_sentiment': final_sentiment,
            'confidence': confidence
        }
    
    def _aggregate_results(self, results: Dict) -> tuple:
        """
        Tổng hợp kết quả từ nhiều phương pháp
        
        Returns:
            (final_sentiment, confidence)
        """
        if not results:
            return 'neutral', 0.0
        
        # Đếm votes
        sentiments = [r['sentiment'] for r in results.values()]
        
        # Ưu tiên theo độ chính xác: PhoBERT > underthesea > VADER
        if 'phobert_vi' in results:
            return results['phobert_vi']['sentiment'], results['phobert_vi']['confidence']
        
        if 'underthesea_vi' in results and len(results) == 1:
            # Chỉ có underthesea, dùng luôn
            return results['underthesea_vi']['sentiment'], results['underthesea_vi']['confidence']
        
        # Voting: sentiment nào nhiều nhất
        sentiment_counts = {
            'positive': sentiments.count('positive'),
            'negative': sentiments.count('negative'),
            'neutral': sentiments.count('neutral')
        }
        
        final_sentiment = max(sentiment_counts, key=sentiment_counts.get)
        
        # Tính confidence trung bình
        confidences = [r.get('confidence', 0) for r in results.values()]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return final_sentiment, avg_confidence
    
    def analyze_comments(self, comments: List[Dict]) -> Dict:
        """
        Phân tích sentiment cho một list comments
        
        Args:
            comments: List các dictionary chứa comment data
            
        Returns:
            Dictionary chứa kết quả phân tích tổng hợp
        """
        if not comments:
            return {
                'total_comments': 0,
                'analyzed_comments': 0,
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                'sentiment_percentage': {'positive': 0, 'negative': 0, 'neutral': 0},
                'avg_confidence': 0.0,
                'comments_analysis': []
            }
        
        print(f" Đang phân tích {len(comments)} comments...")
        
        analyzed = []
        for comment in comments:
            text = comment.get('text', '')
            if text:
                analysis = self.analyze_text(text)
                analysis['comment_id'] = comment.get('comment_id')
                analysis['likes'] = comment.get('likes', 0)
                analyzed.append(analysis)
        
        # Tính toán phân phối
        sentiment_counts = {
            'positive': sum(1 for a in analyzed if a['final_sentiment'] == 'positive'),
            'negative': sum(1 for a in analyzed if a['final_sentiment'] == 'negative'),
            'neutral': sum(1 for a in analyzed if a['final_sentiment'] == 'neutral')
        }
        
        total = len(analyzed)
        sentiment_percentage = {
            'positive': (sentiment_counts['positive'] / total * 100) if total > 0 else 0,
            'negative': (sentiment_counts['negative'] / total * 100) if total > 0 else 0,
            'neutral': (sentiment_counts['neutral'] / total * 100) if total > 0 else 0
        }
        
        avg_confidence = sum(a['confidence'] for a in analyzed) / total if total > 0 else 0
        
        return {
            'total_comments': len(comments),
            'analyzed_comments': total,
            'sentiment_distribution': sentiment_counts,
            'sentiment_percentage': sentiment_percentage,
            'avg_confidence': avg_confidence,
            'comments_analysis': analyzed
        }
    
    def analyze_video_sentiment(self, video_data: Dict) -> Dict:
        """
        Phân tích sentiment cho một video (description + comments)
        
        Args:
            video_data: Dictionary chứa thông tin video
            
        Returns:
            Dictionary chứa kết quả phân tích
        """
        result = {
            'video_id': video_data.get('video_id'),
            'video_url': video_data.get('video_url'),
        }
        
        # Phân tích description
        description = video_data.get('description', '')
        if description:
            result['description_sentiment'] = self.analyze_text(description)
        
        # Phân tích comments
        comments = video_data.get('comments', [])
        result['comments_sentiment'] = self.analyze_comments(comments)
        
        # Tính overall sentiment score
        desc_score = 0
        if description:
            sentiment = result.get('description_sentiment', {}).get('final_sentiment', 'neutral')
            desc_score = 1 if sentiment == 'positive' else -1 if sentiment == 'negative' else 0
        
        comment_dist = result['comments_sentiment']['sentiment_distribution']
        comment_score = (comment_dist['positive'] - comment_dist['negative']) / max(result['comments_sentiment']['analyzed_comments'], 1)
        
        # Weighted average (comments có trọng số cao hơn)
        overall_score = (desc_score * 0.2 + comment_score * 0.8)
        
        if overall_score > 0.1:
            overall_sentiment = 'positive'
        elif overall_score < -0.1:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        result['overall_sentiment'] = overall_sentiment
        result['overall_score'] = overall_score
        
        return result
    
    def analyze_profile_sentiment(self, profile_data: Dict) -> Dict:
        """
        Phân tích sentiment cho toàn bộ profile
        
        Args:
            profile_data: Dictionary chứa dữ liệu profile từ TikTokScraper
            
        Returns:
            Dictionary chứa kết quả phân tích sentiment tổng hợp
        """
        videos = profile_data.get('videos', [])
        
        print(f"\n{'='*60}")
        print(f" PHÂN TÍCH CẢM XÚC NGƯỜI DÙNG")
        print(f"{'='*60}\n")
        print(f" Đang phân tích sentiment cho {len(videos)} videos...")
        
        video_sentiments = []
        for i, video in enumerate(videos, 1):
            print(f"  → Video {i}/{len(videos)}...", end='\r')
            sentiment = self.analyze_video_sentiment(video)
            video_sentiments.append(sentiment)
        
        print(f"✓ Hoàn thành phân tích sentiment!{' '*30}")
        
        # Tổng hợp
        total_positive = sum(1 for v in video_sentiments if v['overall_sentiment'] == 'positive')
        total_negative = sum(1 for v in video_sentiments if v['overall_sentiment'] == 'negative')
        total_neutral = sum(1 for v in video_sentiments if v['overall_sentiment'] == 'neutral')
        
        total_comments = sum(v['comments_sentiment']['analyzed_comments'] for v in video_sentiments)
        total_positive_comments = sum(v['comments_sentiment']['sentiment_distribution']['positive'] for v in video_sentiments)
        total_negative_comments = sum(v['comments_sentiment']['sentiment_distribution']['negative'] for v in video_sentiments)
        total_neutral_comments = sum(v['comments_sentiment']['sentiment_distribution']['neutral'] for v in video_sentiments)
        
        return {
            'username': profile_data.get('username'),
            'total_videos_analyzed': len(videos),
            'video_sentiment_distribution': {
                'positive': total_positive,
                'negative': total_negative,
                'neutral': total_neutral
            },
            'video_sentiment_percentage': {
                'positive': (total_positive / len(videos) * 100) if videos else 0,
                'negative': (total_negative / len(videos) * 100) if videos else 0,
                'neutral': (total_neutral / len(videos) * 100) if videos else 0
            },
            'comments_sentiment_distribution': {
                'positive': total_positive_comments,
                'negative': total_negative_comments,
                'neutral': total_neutral_comments,
                'total': total_comments
            },
            'comments_sentiment_percentage': {
                'positive': (total_positive_comments / total_comments * 100) if total_comments > 0 else 0,
                'negative': (total_negative_comments / total_comments * 100) if total_comments > 0 else 0,
                'neutral': (total_neutral_comments / total_comments * 100) if total_comments > 0 else 0
            },
            'video_sentiments': video_sentiments
        }
