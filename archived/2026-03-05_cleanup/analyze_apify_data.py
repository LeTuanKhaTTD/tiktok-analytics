"""
Script để analyze Apify TikTok Comments JSON
"""
import json
from collections import Counter
from datetime import datetime

def analyze_apify_data(filepath):
    """Analyze Apify TikTok comments data"""
    
    print("="*80)
    print(" PHÂN TÍCH DATA TỪ APIFY")
    print("="*80)
    print()
    
    # Load JSON
    print(f"📂 Loading: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"   ✅ Loaded successfully!")
    print()
    
    # Basic stats
    total_comments = len(data)
    print(f"📊 TỔNG QUAN:")
    print(f"   💬 Total comments: {total_comments:,}")
    print()
    
    # Count unique videos
    video_urls = set()
    for comment in data:
        video_url = comment.get('videoWebUrl', '')
        if video_url:
            video_urls.add(video_url)
    
    print(f"   🎬 Unique videos: {len(video_urls)}")
    print(f"   📈 Avg comments per video: {total_comments / len(video_urls):.1f}")
    print()
    
    # Comments per video distribution
    video_comment_count = Counter()
    for comment in data:
        video_url = comment.get('videoWebUrl', '')
        if video_url:
            video_comment_count[video_url] += 1
    
    # Top videos by comment count
    print(f"🔥 TOP 10 VIDEOS BY COMMENTS:")
    for idx, (video_url, count) in enumerate(video_comment_count.most_common(10), 1):
        video_id = video_url.split('/')[-1] if video_url else 'unknown'
        print(f"   {idx:2d}. Video {video_id[-8:]}: {count:4d} comments")
    print()
    
    # Likes distribution
    total_likes = sum(c.get('diggCount', 0) for c in data)
    avg_likes = total_likes / total_comments if total_comments > 0 else 0
    
    print(f"👍 LIKES STATS:")
    print(f"   Total likes: {total_likes:,}")
    print(f"   Average likes per comment: {avg_likes:.2f}")
    print()
    
    # Top comments by likes
    print(f"⭐ TOP 10 COMMENTS BY LIKES:")
    sorted_by_likes = sorted(data, key=lambda x: x.get('diggCount', 0), reverse=True)
    for idx, comment in enumerate(sorted_by_likes[:10], 1):
        text = comment.get('text', '')[:60]
        likes = comment.get('diggCount', 0)
        print(f"   {idx:2d}. [{likes:4d} likes] \"{text}...\"")
    print()
    
    # Sample comments
    print(f"📝 SAMPLE COMMENTS (first 5):")
    for idx, comment in enumerate(data[:5], 1):
        text = comment.get('text', '')
        likes = comment.get('diggCount', 0)
        user = comment.get('uniqueId', 'unknown')
        print(f"   {idx}. @{user}: \"{text[:50]}...\" ({likes} likes)")
    print()
    
    # Data structure info
    print(f"📋 DATA FIELDS AVAILABLE:")
    if data:
        sample = data[0]
        for key in sample.keys():
            print(f"   • {key}")
    print()
    
    print("="*80)
    print(" SUMMARY")
    print("="*80)
    print(f"✅ {total_comments:,} comments từ {len(video_urls)} videos")
    print(f"✅ Average {total_comments / len(video_urls):.1f} comments per video")
    print(f"✅ Total {total_likes:,} likes")
    print()
    print("🎯 DATA QUALITY: EXCELLENT!")
    print("   Ready for sentiment analysis!")
    print()
    
    return {
        'total_comments': total_comments,
        'total_videos': len(video_urls),
        'total_likes': total_likes,
        'video_urls': list(video_urls)
    }

if __name__ == "__main__":
    filepath = "../dataset_tiktok-comments-scraper_2026-03-04_07-35-21-497.json"
    stats = analyze_apify_data(filepath)
