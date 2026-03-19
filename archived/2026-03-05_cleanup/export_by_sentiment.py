"""
Export Comments by Sentiment - Chia comments theo sắc thái
Xuất ra các file riêng: positive, negative, neutral
"""
import json
from datetime import datetime
import os

def export_by_sentiment(input_file):
    """
    Chia comments thành các file theo sentiment
    """
    print("="*80)
    print(" XUẤT FILE THEO SẮC THÁI - EXPORT BY SENTIMENT")
    print("="*80)
    print()
    
    # Load data
    print(f"📂 Loading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Flatten comments from videos structure
    all_comments = []
    if 'videos' in data:
        for video in data['videos']:
            for comment in video.get('comments', []):
                # Add video context to comment
                comment['video_id'] = video.get('video_id')
                comment['video_url'] = video.get('video_url')
                all_comments.append(comment)
    else:
        all_comments = data.get('comments', [])
    
    total = len(all_comments)
    print(f"   ✅ Loaded {total:,} comments")
    print()
    
    # Separate by sentiment
    positive_comments = [c for c in all_comments if c.get('sentiment') == 'positive']
    negative_comments = [c for c in all_comments if c.get('sentiment') == 'negative']
    neutral_comments = [c for c in all_comments if c.get('sentiment') == 'neutral']
    
    print(f"📊 Phân loại:")
    print(f"   ✅ Positive: {len(positive_comments):,} comments ({len(positive_comments)/total*100:.1f}%)")
    print(f"   ❌ Negative: {len(negative_comments):,} comments ({len(negative_comments)/total*100:.1f}%)")
    print(f"   ⚪ Neutral:  {len(neutral_comments):,} comments ({len(neutral_comments)/total*100:.1f}%)")
    print()
    
    # Create output directory
    output_dir = "data/sentiment_export"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export functions
    def export_json(comments, filename, sentiment_type, emoji):
        """Export comments to JSON"""
        # Sort by likes (descending)
        sorted_comments = sorted(comments, key=lambda x: x.get('likes', 0), reverse=True)
        
        output_data = {
            "sentiment": sentiment_type,
            "total_comments": len(comments),
            "percentage": len(comments) / total * 100,
            "exported_at": datetime.now().isoformat(),
            "model": data.get('model', 'PhoBERT'),
            "accuracy": data.get('accuracy', '~92%'),
            "statistics": {
                "total_likes": sum(c.get('likes', 0) for c in comments),
                "avg_likes": sum(c.get('likes', 0) for c in comments) / len(comments) if comments else 0,
                "avg_confidence": sum(c.get('confidence', 0) for c in comments) / len(comments) if comments else 0,
                "top_comment_likes": sorted_comments[0].get('likes', 0) if sorted_comments else 0
            },
            "comments": sorted_comments
        }
        
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"   {emoji} Saved: {filepath}")
        return filepath
    
    def export_txt(comments, filename, sentiment_type, emoji):
        """Export comments to readable text file"""
        # Sort by likes
        sorted_comments = sorted(comments, key=lambda x: x.get('likes', 0), reverse=True)
        
        lines = []
        lines.append("="*80)
        lines.append(f" {sentiment_type.upper()} COMMENTS - {emoji}")
        lines.append("="*80)
        lines.append("")
        lines.append(f"Tổng số: {len(comments):,} comments ({len(comments)/total*100:.1f}%)")
        lines.append(f"Model: {data.get('model', 'PhoBERT')} | Accuracy: {data.get('accuracy', '~92%')}")
        lines.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("-"*80)
        lines.append("")
        
        for idx, comment in enumerate(sorted_comments, 1):
            text = comment.get('text', '')
            likes = comment.get('likes', 0)
            confidence = comment.get('confidence', 0)
            video_id = comment.get('video_id', 'unknown')
            
            lines.append(f"{idx}. [{likes:,} likes | Confidence: {confidence:.0%}]")
            lines.append(f"   \"{text}\"")
            lines.append(f"   Video: {video_id}")
            lines.append("")
        
        lines.append("="*80)
        lines.append(f" END OF {sentiment_type.upper()} COMMENTS")
        lines.append("="*80)
        
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"   📄 Saved: {filepath}")
        return filepath
    
    # Export files
    print("💾 Exporting files...")
    print()
    
    print("📁 POSITIVE Comments:")
    export_json(positive_comments, f"positive_comments_{timestamp}.json", "positive", "✅")
    export_txt(positive_comments, f"positive_comments_{timestamp}.txt", "positive", "✅")
    print()
    
    print("📁 NEGATIVE Comments:")
    export_json(negative_comments, f"negative_comments_{timestamp}.json", "negative", "❌")
    export_txt(negative_comments, f"negative_comments_{timestamp}.txt", "negative", "❌")
    print()
    
    print("📁 NEUTRAL Comments:")
    export_json(neutral_comments, f"neutral_comments_{timestamp}.json", "neutral", "⚪")
    export_txt(neutral_comments, f"neutral_comments_{timestamp}.txt", "neutral", "⚪")
    print()
    
    # Export summary
    print("📁 SUMMARY File:")
    summary_data = {
        "total_comments": total,
        "analyzed_at": data.get('analyzed_at'),
        "model": data.get('model', 'PhoBERT'),
        "accuracy": data.get('accuracy', '~92%'),
        "sentiment_distribution": {
            "positive": {
                "count": len(positive_comments),
                "percentage": len(positive_comments) / total * 100,
                "avg_confidence": sum(c.get('confidence', 0) for c in positive_comments) / len(positive_comments) if positive_comments else 0
            },
            "negative": {
                "count": len(negative_comments),
                "percentage": len(negative_comments) / total * 100,
                "avg_confidence": sum(c.get('confidence', 0) for c in negative_comments) / len(negative_comments) if negative_comments else 0
            },
            "neutral": {
                "count": len(neutral_comments),
                "percentage": len(neutral_comments) / total * 100,
                "avg_confidence": sum(c.get('confidence', 0) for c in neutral_comments) / len(neutral_comments) if neutral_comments else 0
            }
        },
        "exported_at": datetime.now().isoformat(),
        "export_location": output_dir
    }
    
    summary_file = os.path.join(output_dir, f"sentiment_summary_{timestamp}.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    print(f"   📊 Saved: {summary_file}")
    print()
    
    print("="*80)
    print(" ✅ COMPLETED!")
    print("="*80)
    print()
    print(f"📁 All files exported to: {output_dir}")
    print()
    print("Files created:")
    print(f"  ✅ positive_comments_{timestamp}.json - {len(positive_comments)} comments")
    print(f"  ✅ positive_comments_{timestamp}.txt  - Readable format")
    print(f"  ❌ negative_comments_{timestamp}.json - {len(negative_comments)} comments")
    print(f"  ❌ negative_comments_{timestamp}.txt  - Readable format")
    print(f"  ⚪ neutral_comments_{timestamp}.json  - {len(neutral_comments)} comments")
    print(f"  ⚪ neutral_comments_{timestamp}.txt   - Readable format")
    print(f"  📊 sentiment_summary_{timestamp}.json - Overview")
    print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "data/tong_hop_comment.json"
    
    export_by_sentiment(input_file)
