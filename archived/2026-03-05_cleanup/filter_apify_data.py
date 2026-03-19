"""
Script để lọc và chuẩn bị data từ Apify cho sentiment analysis
"""
import json
import re
from datetime import datetime

def is_vietnamese(text):
    """Check if text contains Vietnamese characters"""
    vietnamese_chars = ['à', 'á', 'ả', 'ã', 'ạ', 'ă', 'ằ', 'ắ', 'ẳ', 'ẵ', 'ặ',
                       'â', 'ầ', 'ấ', 'ẩ', 'ẫ', 'ậ', 'đ', 'è', 'é', 'ẻ', 'ẽ', 'ẹ',
                       'ê', 'ề', 'ế', 'ể', 'ễ', 'ệ', 'ì', 'í', 'ỉ', 'ĩ', 'ị',
                       'ò', 'ó', 'ỏ', 'õ', 'ọ', 'ô', 'ồ', 'ố', 'ổ', 'ỗ', 'ộ',
                       'ơ', 'ờ', 'ớ', 'ở', 'ỡ', 'ợ', 'ù', 'ú', 'ủ', 'ũ', 'ụ',
                       'ư', 'ừ', 'ứ', 'ử', 'ữ', 'ự', 'ỳ', 'ý', 'ỷ', 'ỹ', 'ỵ']
    
    text_lower = text.lower()
    for char in vietnamese_chars:
        if char in text_lower:
            return True
    return False

def filter_apify_data(input_file, output_file):
    """Filter Apify data to keep only relevant Vietnamese comments"""
    
    print("="*80)
    print(" LỌC VÀ CHUẨN HÓA DATA")
    print("="*80)
    print()
    
    # Load data
    print(f"📂 Loading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"   ✅ Loaded {len(data):,} comments")
    print()
    
    # Filter criteria
    filtered_comments = []
    stats = {
        'total': len(data),
        'vietnamese': 0,
        'english': 0,
        'short': 0,  # Too short (< 2 chars)
        'valid': 0
    }
    
    print("🔍 Filtering...")
    for comment in data:
        text = comment.get('text', '')
        
        # Skip too short
        if len(text.strip()) < 2:
            stats['short'] += 1
            continue
        
        # Check language
        if is_vietnamese(text):
            stats['vietnamese'] += 1
            
            # Transform to standard format
            filtered_comment = {
                'text': text.strip(),
                'author': comment.get('uniqueId', 'unknown'),
                'likes': comment.get('diggCount', 0),
                'video_id': comment.get('videoWebUrl', '').split('/')[-1] if comment.get('videoWebUrl') else 'unknown',
                'video_url': comment.get('videoWebUrl', ''),
                'created_at': comment.get('createTimeISO', '')
            }
            
            filtered_comments.append(filtered_comment)
            stats['valid'] += 1
        else:
            stats['english'] += 1
    
    print(f"   ✅ Filtering complete!")
    print()
    
    # Statistics
    print("📊 STATISTICS:")
    print(f"   Total comments: {stats['total']:,}")
    print(f"   Vietnamese: {stats['vietnamese']:,} ({stats['vietnamese']/stats['total']*100:.1f}%)")
    print(f"   English/Other: {stats['english']:,} ({stats['english']/stats['total']*100:.1f}%)")
    print(f"   Too short: {stats['short']:,}")
    print(f"   Valid for analysis: {stats['valid']:,}")
    print()
    
    # Count unique videos
    unique_videos = len(set(c['video_id'] for c in filtered_comments))
    print(f"   🎬 From {unique_videos} unique videos")
    print(f"   📈 Avg {stats['valid']/unique_videos:.1f} comments per video")
    print()
    
    # Top comments by likes
    print("⭐ TOP 10 VIETNAMESE COMMENTS BY LIKES:")
    sorted_by_likes = sorted(filtered_comments, key=lambda x: x['likes'], reverse=True)
    for idx, comment in enumerate(sorted_by_likes[:10], 1):
        text = comment['text'][:60]
        likes = comment['likes']
        print(f"   {idx:2d}. [{likes:5d} likes] \"{text}...\"")
    print()
    
    # Sample comments
    print("📝 SAMPLE COMMENTS:")
    for idx, comment in enumerate(filtered_comments[:5], 1):
        print(f"   {idx}. @{comment['author']}: \"{comment['text'][:50]}...\"")
    print()
    
    # Save filtered data
    output_data = {
        'username': '@travinhuniversity',
        'total_comments': len(filtered_comments),
        'total_videos': unique_videos,
        'collected_at': datetime.now().isoformat(),
        'source': 'apify',
        'comments': filtered_comments
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved to: {output_file}")
    print()
    
    print("="*80)
    print(" SUMMARY")
    print("="*80)
    print(f"✅ Filtered: {stats['valid']:,} Vietnamese comments")
    print(f"✅ From: {unique_videos} videos")
    print(f"✅ Ready for sentiment analysis!")
    print()
    
    return output_data

if __name__ == "__main__":
    input_file = "../dataset_tiktok-comments-scraper_2026-03-04_07-35-21-497.json"
    output_file = "data/tiktok_travinhuniversity_apify_filtered.json"
    
    import os
    os.makedirs("data", exist_ok=True)
    
    result = filter_apify_data(input_file, output_file)
    
    print("🎯 NEXT STEP:")
    print(f"   python visualize_sentiment.py {output_file}")
    print()
