"""
Script organize comments theo từng video và sort theo thứ tự
"""
import json
from collections import defaultdict
from datetime import datetime

def organize_comments_by_video(input_file, output_file):
    """Organize comments by video"""
    
    print("="*80)
    print(" ORGANIZE COMMENTS BY VIDEO")
    print("="*80)
    print()
    
    # Load data
    print(f"📂 Loading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    comments = data.get('comments', [])
    print(f"   ✅ Loaded {len(comments):,} comments")
    print()
    
    # Group by video
    print("📊 Organizing by video...")
    videos = defaultdict(list)
    
    for comment in comments:
        video_id = comment.get('video_id', 'unknown')
        videos[video_id].append(comment)
    
    print(f"   ✅ Found {len(videos)} unique videos")
    print()
    
    # Convert to list and sort by comment count
    video_list = []
    for video_id, video_comments in videos.items():
        # Get video URL from first comment
        video_url = video_comments[0].get('video_url', '') if video_comments else ''
        
        # Calculate stats
        total_likes = sum(c.get('likes', 0) for c in video_comments)
        avg_likes = total_likes / len(video_comments) if video_comments else 0
        
        video_data = {
            'video_id': video_id,
            'video_url': video_url,
            'comments_count': len(video_comments),
            'total_likes': total_likes,
            'avg_likes_per_comment': round(avg_likes, 2),
            'comments': sorted(video_comments, key=lambda x: x.get('likes', 0), reverse=True)
        }
        
        video_list.append(video_data)
    
    # Sort videos by comment count (descending)
    video_list.sort(key=lambda x: x['comments_count'], reverse=True)
    
    # Print summary
    print("🎬 TOP 20 VIDEOS BY COMMENT COUNT:")
    for idx, video in enumerate(video_list[:20], 1):
        vid = video['video_id'][-8:] if len(video['video_id']) > 8 else video['video_id']
        count = video['comments_count']
        likes = video['total_likes']
        print(f"   {idx:2d}. Video {vid}: {count:4d} comments, {likes:,} total likes")
    print()
    
    # Calculate totals
    total_comments = sum(v['comments_count'] for v in video_list)
    total_likes = sum(v['total_likes'] for v in video_list)
    
    print("📊 STATISTICS:")
    print(f"   Total videos: {len(video_list)}")
    print(f"   Total comments: {total_comments:,}")
    print(f"   Total likes: {total_likes:,}")
    print(f"   Avg comments per video: {total_comments / len(video_list):.1f}")
    print()
    
    # Save organized data
    output_data = {
        'username': data.get('username', '@travinhuniversity'),
        'total_videos': len(video_list),
        'total_comments': total_comments,
        'total_likes': total_likes,
        'organized_at': datetime.now().isoformat(),
        'source': 'apify',
        'videos': video_list
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved organized data: {output_file}")
    print()
    
    # Show sample from top video
    if video_list:
        top_video = video_list[0]
        print(f"📝 SAMPLE - TOP VIDEO (Video {top_video['video_id'][-8:]}):")
        print(f"   URL: {top_video['video_url']}")
        print(f"   Comments: {top_video['comments_count']}")
        print()
        print("   Top 5 comments:")
        for idx, comment in enumerate(top_video['comments'][:5], 1):
            text = comment.get('text', '')[:60]
            likes = comment.get('likes', 0)
            print(f"   {idx}. [{likes:5d} likes] \"{text}...\"")
        print()
    
    print("="*80)
    print(" ✅ ORGANIZED!")
    print("="*80)
    print()
    print(f"Data structure:")
    print(f"  • {len(video_list)} videos")
    print(f"  • Each video has list of comments sorted by likes")
    print(f"  • Videos sorted by comment count")
    print()
    
    return output_data

if __name__ == "__main__":
    input_file = "data/tiktok_travinhuniversity_apify_filtered.json"
    output_file = "data/tiktok_travinhuniversity_apify_organized.json"
    
    result = organize_comments_by_video(input_file, output_file)
    
    print("🎯 NEXT STEPS:")
    print(f"   1. Run sentiment analysis:")
    print(f"      python run_sentiment_analysis.py {output_file}")
    print()
    print(f"   2. Or use for analysis directly")
    print()
