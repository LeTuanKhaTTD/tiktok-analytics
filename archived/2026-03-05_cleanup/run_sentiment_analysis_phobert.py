"""
Sentiment Analysis using PhoBERT for organized TikTok comments
Uses VinAI's PhoBERT model for 92% accuracy on Vietnamese text
"""
import json
import sys
from datetime import datetime
import os

# Import sentiment analyzer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.sentiment_analyzer import SentimentAnalyzer

def analyze_organized_data(input_file):
    """
    Analyze sentiment for organized comments (by video structure)
    Uses PhoBERT for high accuracy Vietnamese sentiment analysis
    """
    
    print("="*80)
    print(" PHÂN TÍCH SẮC THÁI COMMENTS - PHOBERT MODEL (92% ACCURACY)")
    print("="*80)
    print()
    
    # Load data
    print(f"📂 Loading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    videos = data.get('videos', [])
    total_videos = len(videos)
    total_comments = data.get('total_comments', 0)
    
    print(f"   ✅ Loaded {total_videos:,} videos with {total_comments:,} comments")
    print()
    
    if total_comments == 0:
        print("❌ No comments found!")
        return
    
    # Initialize PhoBERT sentiment analyzer
    print("🤖 Loading PhoBERT model (Vietnamese sentiment analysis)...")
    print("   First time will download ~400MB model, subsequent runs use cache")
    print()
    analyzer = SentimentAnalyzer(use_vietnamese=True, use_transformers=True)
    print()
    
    # Analyze comments in each video
    print(f"📊 Analyzing {total_comments:,} comments across {total_videos} videos...")
    print("   This will take 1-2 minutes with PhoBERT...")
    print()
    
    # Global sentiment counts
    global_sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    processed_comments = 0
    
    # Process each video
    for video_idx, video in enumerate(videos, 1):
        video_id = video.get('video_id', 'unknown')
        comments = video.get('comments', [])
        
        # Video-level sentiment counts
        video_sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        # Analyze each comment in this video
        for comment in comments:
            text = comment.get('text', '')
            
            # Analyze sentiment with PhoBERT
            result = analyzer.analyze_text(text)
            
            # Add sentiment fields to comment
            comment['sentiment'] = result['final_sentiment']
            comment['confidence'] = result.get('confidence', 0)
            comment['language'] = result.get('language', 'vi')
            
            # Update counts
            sentiment = result['final_sentiment']
            video_sentiment_counts[sentiment] += 1
            global_sentiment_counts[sentiment] += 1
            
            processed_comments += 1
            
            # Progress indicator
            if processed_comments % 100 == 0 or processed_comments == total_comments:
                progress_pct = processed_comments / total_comments * 100
                print(f"   Progress: {processed_comments}/{total_comments} ({progress_pct:.1f}%) - Video {video_idx}/{total_videos}")
        
        # Add sentiment summary to video
        video['sentiment_summary'] = video_sentiment_counts
        video['sentiment_percentages'] = {
            'positive': (video_sentiment_counts['positive'] / len(comments) * 100) if len(comments) > 0 else 0,
            'negative': (video_sentiment_counts['negative'] / len(comments) * 100) if len(comments) > 0 else 0,
            'neutral': (video_sentiment_counts['neutral'] / len(comments) * 100) if len(comments) > 0 else 0
        }
    
    print()
    print("   ✅ Analysis complete!")
    print()
    
    # Calculate global percentages
    global_sentiment_percentages = {
        'positive': (global_sentiment_counts['positive'] / total_comments * 100) if total_comments > 0 else 0,
        'negative': (global_sentiment_counts['negative'] / total_comments * 100) if total_comments > 0 else 0,
        'neutral': (global_sentiment_counts['neutral'] / total_comments * 100) if total_comments > 0 else 0
    }
    
    # Print summary
    print("="*80)
    print(" KẾT QUẢ PHÂN TÍCH - PHOBERT MODEL")
    print("="*80)
    print()
    print(f"📊 TỔNG QUAN:")
    print(f"   Total videos: {total_videos:,}")
    print(f"   Total comments: {total_comments:,}")
    print(f"   Model: PhoBERT (wonrax/phobert-base-vietnamese-sentiment)")
    print(f"   Accuracy: ~92% for Vietnamese text")
    print()
    print(f"   ✅ Positive: {global_sentiment_counts['positive']:5d} ({global_sentiment_percentages['positive']:.1f}%)")
    print(f"   ⚪ Neutral:  {global_sentiment_counts['neutral']:5d} ({global_sentiment_percentages['neutral']:.1f}%)")
    print(f"   ❌ Negative: {global_sentiment_counts['negative']:5d} ({global_sentiment_percentages['negative']:.1f}%)")
    print()
    
    # Collect all comments with sentiment for top analysis
    all_comments = []
    for video in videos:
        all_comments.extend(video.get('comments', []))
    
    # Top positive comments
    positive_comments = [c for c in all_comments if c.get('sentiment') == 'positive']
    if positive_comments:
        sorted_positive = sorted(positive_comments, key=lambda x: x.get('likes', 0), reverse=True)[:5]
        print("🌟 TOP 5 POSITIVE COMMENTS:")
        for idx, c in enumerate(sorted_positive, 1):
            text = c.get('text', '')[:70]
            likes = c.get('likes', 0)
            confidence = c.get('confidence', 0)
            print(f"   {idx}. [{likes:5d} likes | {confidence:.0%} confidence] \"{text}...\"")
        print()
    
    # Top negative comments
    negative_comments = [c for c in all_comments if c.get('sentiment') == 'negative']
    if negative_comments:
        sorted_negative = sorted(negative_comments, key=lambda x: x.get('likes', 0), reverse=True)[:5]
        print("⚠️  TOP 5 NEGATIVE COMMENTS (Cần xử lý):")
        for idx, c in enumerate(sorted_negative, 1):
            text = c.get('text', '')[:70]
            likes = c.get('likes', 0)
            confidence = c.get('confidence', 0)
            print(f"   {idx}. [{likes:5d} likes | {confidence:.0%} confidence] \"{text}...\"")
        print()
    
    # Videos with most negative sentiment
    videos_by_negative = sorted(
        videos, 
        key=lambda v: v['sentiment_summary']['negative'], 
        reverse=True
    )[:5]
    
    print("📹 TOP 5 VIDEOS WITH MOST NEGATIVE COMMENTS:")
    for idx, video in enumerate(videos_by_negative, 1):
        video_id = video.get('video_id')
        neg_count = video['sentiment_summary']['negative']
        total_count = len(video.get('comments', []))
        neg_pct = video['sentiment_percentages']['negative']
        print(f"   {idx}. Video {video_id}: {neg_count}/{total_count} negative ({neg_pct:.1f}%)")
    print()
    
    # Save results with sentiment data
    output_file = input_file.replace('.json', '_sentiment.json')
    
    output_data = {
        'username': data.get('username'),
        'total_videos': total_videos,
        'total_comments': total_comments,
        'total_likes': data.get('total_likes', 0),
        'source': data.get('source', 'apify'),
        'analyzed_at': datetime.now().isoformat(),
        'model': 'PhoBERT (wonrax/phobert-base-vietnamese-sentiment)',
        'accuracy': '~92% for Vietnamese',
        'global_sentiment_summary': {
            'positive': {
                'count': global_sentiment_counts['positive'],
                'percentage': global_sentiment_percentages['positive']
            },
            'negative': {
                'count': global_sentiment_counts['negative'],
                'percentage': global_sentiment_percentages['negative']
            },
            'neutral': {
                'count': global_sentiment_counts['neutral'],
                'percentage': global_sentiment_percentages['neutral']
            }
        },
        'videos': videos
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved to: {output_file}")
    print()
    
    print("="*80)
    print(" ✅ COMPLETED!")
    print("="*80)
    print()
    print(f"Next step: Visualize results")
    print(f"   python visualize_sentiment.py {output_file}")
    print()
    
    return output_data

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "data/tiktok_travinhuniversity_apify_organized.json"
    
    analyze_organized_data(input_file)
