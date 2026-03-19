"""Phân tích toàn diện TikTok - Video engagement + Comment sentiment

Module này phân tích dữ liệu đã ghép (merged) và xuất báo cáo text:

Phần 1: Phân tích tương tác video (Video Engagement)
  - Tổng quan: plays, likes, comments, shares, saves
  - Tỷ lệ tương tác trung bình (engagement rate)
  - Top 10 video theo lượt xem và engagement rate

Phần 2: Phân tích sắc thái văn bản (Sentiment Analysis)
  - Phân phối sentiment (positive/neutral/negative)
  - Phân bổ theo confidence (high/medium/low)
  - Top bình luận tích cực và tiêu cực

Phần 3: Phân tích kết hợp (Engagement x Sentiment)
  - Video có engagement cao + sentiment tích cực
  - Video cần quan tâm (engagement cao + sentiment tiêu cực)
"""
import json
import sys
from pathlib import Path
from datetime import datetime

def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def analyze_comprehensive(data_file):
    """Phân tích toàn diện: Video engagement + Comment sentiment
    
    Args:
        data_file: Đường dẫn đến file JSON đã ghép (merged)
    """
    
    print("\n")
    print("=" * 80)
    print("PHAN TICH TOAN DIEN TIKTOK - COMPREHENSIVE ANALYTICS".center(80))
    print("=" * 80)
    print()
    
    # Load data
    print(f"[INFO] Loading data from: {data_file}")
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    videos = data.get('videos', [])
    comments = data.get('comments', [])
    metadata = data.get('metadata', {})
    
    print(f"[OK] Loaded: {len(videos)} videos, {len(comments)} comments")
    print()
    
    # ========================================================================
    # PHẦN 1: PHÂN TÍCH VIDEO ENGAGEMENT (Tương tác)
    # ========================================================================
    
    print_header("PHAN 1: PHAN TICH TUONG TAC VIDEO (VIDEO ENGAGEMENT)")
    
    # Tính toán stats tổng quan
    total_plays = sum(v.get('stats', {}).get('play_count', 0) for v in videos)
    total_likes = sum(v.get('stats', {}).get('like_count', 0) for v in videos)
    total_comments = sum(v.get('stats', {}).get('comment_count', 0) for v in videos)
    total_shares = sum(v.get('stats', {}).get('share_count', 0) for v in videos)
    total_collects = sum(v.get('stats', {}).get('collect_count', 0) for v in videos)
    
    print("\n1.1 TONG QUAN TUONG TAC:")
    print(f"   [PLAYS] Total Plays:      {total_plays:>15,}")
    print(f"   [LIKES] Total Likes:      {total_likes:>15,}")
    print(f"   [COMMENTS] Total Comments:   {total_comments:>15,}")
    print(f"   [SHARES] Total Shares:     {total_shares:>15,}")
    print(f"   [SAVES] Total Saves:      {total_collects:>15,}")
    print()
    
    # Tính engagement rate trung bình
    if total_plays > 0:
        avg_engagement_rate = ((total_likes + total_comments + total_shares) / total_plays) * 100
        avg_like_rate = (total_likes / total_plays) * 100
        avg_comment_rate = (total_comments / total_plays) * 100
        avg_share_rate = (total_shares / total_plays) * 100
        
        print("1.2 TY LE TUONG TAC TRUNG BINH:")
        print(f"   [ENGAGEMENT] Engagement Rate:  {avg_engagement_rate:>10.2f}%")
        print(f"   [LIKE] Like Rate:        {avg_like_rate:>10.2f}%")
        print(f"   [COMMENT] Comment Rate:     {avg_comment_rate:>10.2f}%")
        print(f"   [SHARE] Share Rate:       {avg_share_rate:>10.2f}%")
        print()
    
    # Top videos by engagement
    videos_sorted = sorted(
        videos,
        key=lambda v: v.get('stats', {}).get('play_count', 0),
        reverse=True
    )
    
    print("1.3 TOP 10 VIDEOS THEO LUOT XEM:")
    print(f"{'Rank':<6} {'Video ID':<20} {'Plays':>12} {'Likes':>10} {'Comments':>10} {'Shares':>10} {'Engagement':>12}")
    print("-" * 90)
    
    for i, video in enumerate(videos_sorted[:10], 1):
        stats = video.get('stats', {})
        metrics = video.get('metrics', {})
        print(f"{i:<6} {video.get('id', 'N/A'):<20} "
              f"{stats.get('play_count', 0):>12,} "
              f"{stats.get('like_count', 0):>10,} "
              f"{stats.get('comment_count', 0):>10,} "
              f"{stats.get('share_count', 0):>10,} "
              f"{metrics.get('engagement_rate', 0):>11.2f}%")
    print()
    
    # Top videos by engagement rate
    videos_by_engagement = sorted(
        [v for v in videos if v.get('stats', {}).get('play_count', 0) >= 1000],
        key=lambda v: v.get('metrics', {}).get('engagement_rate', 0),
        reverse=True
    )
    
    print("1.4 TOP 10 VIDEOS THEO ENGAGEMENT RATE (min 1K plays):")
    print(f"{'Rank':<6} {'Video ID':<20} {'Plays':>12} {'Eng. Rate':>12} {'Like Rate':>12} {'Comment Rate':>12}")
    print("-" * 80)
    
    for i, video in enumerate(videos_by_engagement[:10], 1):
        stats = video.get('stats', {})
        metrics = video.get('metrics', {})
        print(f"{i:<6} {video.get('id', 'N/A'):<20} "
              f"{stats.get('play_count', 0):>12,} "
              f"{metrics.get('engagement_rate', 0):>11.2f}% "
              f"{metrics.get('like_rate', 0):>11.2f}% "
              f"{metrics.get('comment_rate', 0):>13.2f}%")
    print()
    
    # ========================================================================
    # PHẦN 2: PHÂN TÍCH SENTIMENT (Sắc thái văn bản)
    # ========================================================================
    
    print_header("PHAN 2: PHAN TICH SAC THAI VAN BAN (SENTIMENT ANALYSIS)")
    
    if not comments:
        print("[WARNING] No comment data available for sentiment analysis")
        return
    
    # Sentiment distribution  
    sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
    for comment in comments:
        sentiment = comment.get('sentiment', 'neutral')
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
    
    total = len(comments)
    
    print("\n2.1 PHAN PHOI SENTIMENT:")
    print(f"   [+] Positive: {sentiment_counts['positive']:>6} ({sentiment_counts['positive']/total*100:>5.1f}%)")
    print(f"   [=] Neutral:  {sentiment_counts['neutral']:>6} ({sentiment_counts['neutral']/total*100:>5.1f}%)")
    print(f"   [-] Negative: {sentiment_counts['negative']:>6} ({sentiment_counts['negative']/total*100:>5.1f}%)")
    print(f"   [TOTAL] Total:    {total:>6} comments")
    print()
    
    # Sentiment by confidence
    high_conf = [c for c in comments if c.get('confidence', 0) >= 0.9]
    medium_conf = [c for c in comments if 0.7 <= c.get('confidence', 0) < 0.9]
    low_conf = [c for c in comments if c.get('confidence', 0) < 0.7]
    
    print("2.2 PHAN BO THEO CONFIDENCE:")
    print(f"   [HIGH] High (>=0.9):   {len(high_conf):>5} ({len(high_conf)/total*100:>5.1f}%)")
    print(f"   [MED] Medium (0.7-0.9): {len(medium_conf):>5} ({len(medium_conf)/total*100:>5.1f}%)")
    print(f"   [LOW] Low (<0.7):    {len(low_conf):>5} ({len(low_conf)/total*100:>5.1f}%)")
    print()
    
    # Average confidence by sentiment
    pos_conf = [c.get('confidence', 0) for c in comments if c.get('sentiment') == 'positive']
    neu_conf = [c.get('confidence', 0) for c in comments if c.get('sentiment') == 'neutral']
    neg_conf = [c.get('confidence', 0) for c in comments if c.get('sentiment') == 'negative']
    
    print("2.3 CONFIDENCE TRUNG BINH THEO SENTIMENT:")
    if pos_conf:
        print(f"   [+] Positive: {sum(pos_conf)/len(pos_conf):.3f}")
    if neu_conf:
        print(f"   [=] Neutral:  {sum(neu_conf)/len(neu_conf):.3f}")
    if neg_conf:
        print(f"   [-] Negative: {sum(neg_conf)/len(neg_conf):.3f}")
    print()
    
    # Top positive comments (by likes)
    positive_comments = [c for c in comments if c.get('sentiment') == 'positive']
    positive_sorted = sorted(positive_comments, key=lambda c: c.get('likes', 0), reverse=True)
    
    print("2.4 TOP 10 POSITIVE COMMENTS (theo likes):")
    print(f"{'Rank':<6} {'Likes':>8} {'Conf.':>6} {'Comment':<60}")
    print("-" * 90)
    
    for i, comment in enumerate(positive_sorted[:10], 1):
        text = comment.get('text', '')[:57] + "..." if len(comment.get('text', '')) > 60 else comment.get('text', '')
        print(f"{i:<6} {comment.get('likes', 0):>8} {comment.get('confidence', 0):>6.2f} {text}")
    print()
    
    # Top negative comments (by likes)  
    negative_comments = [c for c in comments if c.get('sentiment') == 'negative']
    negative_sorted = sorted(negative_comments, key=lambda c: c.get('likes', 0), reverse=True)
    
    print("2.5 TOP 10 NEGATIVE COMMENTS (theo likes):")
    print(f"{'Rank':<6} {'Likes':>8} {'Conf.':>6} {'Comment':<60}")
    print("-" * 90)
    
    for i, comment in enumerate(negative_sorted[:10], 1):
        text = comment.get('text', '')[:57] + "..." if len(comment.get('text', '')) > 60 else comment.get('text', '')
        print(f"{i:<6} {comment.get('likes', 0):>8} {comment.get('confidence', 0):>6.2f} {text}")
    print()
    
    # ========================================================================
    # PHẦN 3: PHÂN TÍCH KẾT HỢP (Video Engagement + Comment Sentiment)
    # ========================================================================
    
    print_header("PHAN 3: PHAN TICH KET HOP (ENGAGEMENT x SENTIMENT)")
    
    # Video sentiment correlation
    video_sentiment_data = []
    
    for video in videos:
        video_id = video.get('id')
        video_comments = [c for c in comments if c.get('video_id') == video_id]
        
        if video_comments:
            pos = sum(1 for c in video_comments if c.get('sentiment') == 'positive')
            neg = sum(1 for c in video_comments if c.get('sentiment') == 'negative')
            total_c = len(video_comments)
            
            sentiment_score = (pos - neg) / total_c if total_c > 0 else 0
            
            video_sentiment_data.append({
                'video_id': video_id,
                'plays': video.get('stats', {}).get('play_count', 0),
                'engagement_rate': video.get('metrics', {}).get('engagement_rate', 0),
                'total_comments': total_c,
                'positive': pos,
                'negative': neg,
                'sentiment_score': sentiment_score
            })
    
    # Top videos by sentiment score (with high engagement)
    high_plays_videos = [v for v in video_sentiment_data if v['plays'] >= 10000]
    best_sentiment = sorted(high_plays_videos, key=lambda v: v['sentiment_score'], reverse=True)
    
    print("\n3.1 TOP VIDEOS: HIGH ENGAGEMENT + POSITIVE SENTIMENT (>=10K plays):")
    print(f"{'Rank':<6} {'Video ID':<20} {'Plays':>12} {'Eng.':>8} {'Pos':>6} {'Neg':>6} {'Score':>8}")
    print("-" * 80)
    
    for i, v in enumerate(best_sentiment[:10], 1):
        print(f"{i:<6} {v['video_id']:<20} "
              f"{v['plays']:>12,} "
              f"{v['engagement_rate']:>7.2f}% "
              f"{v['positive']:>6} "
              f"{v['negative']:>6} "
              f"{v['sentiment_score']:>7.2f}")
    print()
    
    # Videos needing attention (high engagement but negative sentiment)
    worst_sentiment = sorted(high_plays_videos, key=lambda v: v['sentiment_score'])
    
    print("3.2 VIDEOS CAN QUAN TAM: HIGH ENGAGEMENT + NEGATIVE SENTIMENT (>=10K plays):")
    print(f"{'Rank':<6} {'Video ID':<20} {'Plays':>12} {'Eng.':>8} {'Pos':>6} {'Neg':>6} {'Score':>8}")
    print("-" * 80)
    
    for i, v in enumerate(worst_sentiment[:10], 1):
        print(f"{i:<6} {v['video_id']:<20} "
              f"{v['plays']:>12,} "
              f"{v['engagement_rate']:>7.2f}% "
              f"{v['positive']:>6} "
              f"{v['negative']:>6} "
              f"{v['sentiment_score']:>7.2f}")
    print()
    
    # ========================================================================
    # SUMMARY & INSIGHTS
    # ========================================================================
    
    print_header("TOM TAT & GOI Y")
    
    print("\n[KEY INSIGHTS]")
    print()
    
    # Best performing video
    if videos_sorted:
        top_video = videos_sorted[0]
        print(f"1. [TOP] TOP VIDEO:")
        print(f"   Video ID: {top_video.get('id')}")
        print(f"   Plays: {top_video.get('stats', {}).get('play_count', 0):,}")
        print(f"   Engagement: {top_video.get('metrics', {}).get('engagement_rate', 0):.2f}%")
        print()
    
    # Sentiment overall
    pos_pct = sentiment_counts['positive'] / total * 100
    neg_pct = sentiment_counts['negative'] / total * 100
    
    print(f"2. [SENTIMENT] SENTIMENT TONG QUAN:")
    print(f"   {'Tích cực' if pos_pct > 50 else 'Trung tính' if pos_pct > 40 else 'Cần cải thiện'}: {pos_pct:.1f}% positive, {neg_pct:.1f}% negative")
    print()
    
    # Model accuracy
    if metadata.get('model'):
        print(f"3. [MODEL] MODEL ACCURACY:")
        print(f"   {metadata.get('model')} - {metadata.get('accuracy', 'N/A')}")
        print()
    
    print()
    print("=" * 80)
    print("[COMPLETED] PHAN TICH HOAN TAT!")
    print("=" * 80)
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_merged_data.py <data_file.json> [--save]")
        sys.exit(1)
    
    data_file = sys.argv[1]
    if not Path(data_file).exists():
        print(f"Error: File not found: {data_file}")
        sys.exit(1)
    
    # Save to file option
    if len(sys.argv) > 2 and sys.argv[2] == '--save':
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'reports/tiktok_analysis_{timestamp}.txt'
        
        import sys
        from io import StringIO
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        analyze_comprehensive(data_file)
        
        content = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[OK] Report saved to: {output_file}")
    else:
        analyze_comprehensive(data_file)
