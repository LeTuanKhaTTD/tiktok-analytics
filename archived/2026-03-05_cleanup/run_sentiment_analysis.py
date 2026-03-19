"""
Sentiment Analysis cho TikTok comments từ JSON file
"""
import json
import sys
from datetime import datetime
import os

# Import sentiment analyzer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.sentiment_analyzer import SentimentAnalyzer

def analyze_sentiment_from_json(input_file):
    """
    Analyze sentiment for comments in JSON file
    """
    
    print("="*80)
    print(" PHÂN TÍCH SẮC THÁI COMMENTS - SENTIMENT ANALYSIS")
    print("="*80)
    print()
    
    # Load data
    print(f"📂 Loading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    comments = data.get('comments', [])
    total = len(comments)
    
    print(f"   ✅ Loaded {total:,} comments")
    print()
    
    if total == 0:
        print("❌ No comments found!")
        return
    
    # Initialize sentiment analyzer
    print("🤖 Loading PhoBERT model...")
    analyzer = SentimentAnalyzer()
    print("   ✅ Model loaded!")
    print()
    
    # Analyze each comment
    print(f"📊 Analyzing {total:,} comments...")
    print("   This may take a few minutes...")
    print()
    
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    
    for idx, comment in enumerate(comments, 1):
        # Progress indicator
        if idx % 100 == 0 or idx == total:
            print(f"   Progress: {idx}/{total} ({idx/total*100:.1f}%)")
        
        text = comment.get('text', '')
        
        # Analyze sentiment
        result = analyzer.analyze_text(text)
        
        # Add sentiment to comment
        comment['sentiment'] = result['final_sentiment']
        comment['confidence'] = result.get('confidence', 0)
        comment['language'] = result.get('language', 'vi')
        
        # Count
        sentiment_counts[result['final_sentiment']] += 1
    
    print()
    print("   ✅ Analysis complete!")
    print()
    
    # Calculate percentages
    sentiment_percentages = {
        'positive': (sentiment_counts['positive'] / total * 100) if total > 0 else 0,
        'negative': (sentiment_counts['negative'] / total * 100) if total > 0 else 0,
        'neutral': (sentiment_counts['neutral'] / total * 100) if total > 0 else 0
    }
    
    # Print summary
    print("="*80)
    print(" KẾT QUẢ PHÂN TÍCH")
    print("="*80)
    print()
    print(f"📊 TỔNG QUAN:")
    print(f"   Total comments: {total:,}")
    print()
    print(f"   ✅ Positive: {sentiment_counts['positive']:4d} ({sentiment_percentages['positive']:.1f}%)")
    print(f"   ⚪ Neutral:  {sentiment_counts['neutral']:4d} ({sentiment_percentages['neutral']:.1f}%)")
    print(f"   ❌ Negative: {sentiment_counts['negative']:4d} ({sentiment_percentages['negative']:.1f}%)")
    print()
    
    # Top positive comments
    positive_comments = [c for c in comments if c.get('sentiment') == 'positive']
    if positive_comments:
        sorted_positive = sorted(positive_comments, key=lambda x: x.get('likes', 0), reverse=True)[:5]
        print("🌟 TOP 5 POSITIVE COMMENTS:")
        for idx, c in enumerate(sorted_positive, 1):
            text = c.get('text', '')[:60]
            likes = c.get('likes', 0)
            print(f"   {idx}. [{likes:5d} likes] \"{text}...\"")
        print()
    
    # Top negative comments
    negative_comments = [c for c in comments if c.get('sentiment') == 'negative']
    if negative_comments:
        sorted_negative = sorted(negative_comments, key=lambda x: x.get('likes', 0), reverse=True)[:5]
        print("⚠️  TOP 5 NEGATIVE COMMENTS (Cần xử lý):")
        for idx, c in enumerate(sorted_negative, 1):
            text = c.get('text', '')[:60]
            likes = c.get('likes', 0)
            print(f"   {idx}. [{likes:5d} likes] \"{text}...\"")
        print()
    
    # Save results
    output_file = input_file.replace('.json', '_sentiment.json')
    
    output_data = {
        'total_comments': total,
        'sentiment_summary': {
            'positive': {
                'count': sentiment_counts['positive'],
                'percentage': sentiment_percentages['positive']
            },
            'negative': {
                'count': sentiment_counts['negative'],
                'percentage': sentiment_percentages['negative']
            },
            'neutral': {
                'count': sentiment_counts['neutral'],
                'percentage': sentiment_percentages['neutral']
            }
        },
        'analyzed_at': datetime.now().isoformat(),
        'comments': comments
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
        input_file = "data/tiktok_travinhuniversity_apify_filtered.json"
    
    analyze_sentiment_from_json(input_file)
