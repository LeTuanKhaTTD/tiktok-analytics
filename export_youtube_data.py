"""Export YouTube Data - Xuất dữ liệu YouTube sang Excel/CSV"""
import json
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

def export_youtube_data(json_file, output_format='excel'):
    """
    Xuất dữ liệu YouTube từ JSON sang Excel/CSV
    
    Args:
        json_file: Path to YouTube JSON file
        output_format: 'excel', 'csv', or 'both'
    """
    
    print("\n" + "=" * 80)
    print("EXPORT YOUTUBE DATA".center(80))
    print("=" * 80)
    print()
    
    # Load JSON data
    print(f"[INFO] Loading data from: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    channel_info = data.get('channel_info', {})
    videos = data.get('videos', [])
    
    print(f"[OK] Loaded: {len(videos)} videos from channel '{channel_info.get('title', 'Unknown')}'")
    print()
    
    # Channel Info Summary
    print("=" * 80)
    print("CHANNEL INFORMATION")
    print("=" * 80)
    print(f"Channel Name:    {channel_info.get('title', 'N/A')}")
    print(f"Channel ID:      {channel_info.get('channel_id', 'N/A')}")
    print(f"Subscribers:     {channel_info.get('subscriber_count', 0):,}")
    print(f"Total Videos:    {channel_info.get('video_count', 0):,}")
    print(f"Total Views:     {channel_info.get('view_count', 0):,}")
    print(f"Published At:    {channel_info.get('published_at', 'N/A')}")
    print()
    
    # Prepare videos data for export
    videos_data = []
    comments_data = []
    
    for video in videos:
        video_row = {
            'video_id': video.get('video_id', ''),
            'title': video.get('title', ''),
            'published_at': video.get('published_at', ''),
            'duration': video.get('duration', ''),
            'view_count': video.get('view_count', 0),
            'like_count': video.get('like_count', 0),
            'comment_count': video.get('comment_count', 0),
            'favorite_count': video.get('favorite_count', 0),
            'category_id': video.get('category_id', ''),
            'channel_title': video.get('channel_title', ''),
            'thumbnail': video.get('thumbnail', ''),
        }
        
        # Calculate engagement metrics
        views = video.get('view_count', 0)
        likes = video.get('like_count', 0)
        comments = video.get('comment_count', 0)
        
        if views > 0:
            video_row['like_rate'] = (likes / views) * 100
            video_row['comment_rate'] = (comments / views) * 100
            video_row['engagement_rate'] = ((likes + comments) / views) * 100
        else:
            video_row['like_rate'] = 0
            video_row['comment_rate'] = 0
            video_row['engagement_rate'] = 0
        
        videos_data.append(video_row)
        
        # Extract comments
        for comment in video.get('comments', []):
            comment_row = {
                'video_id': video.get('video_id', ''),
                'video_title': video.get('title', ''),
                'comment_id': comment.get('comment_id', ''),
                'author': comment.get('author', ''),
                'text': comment.get('text', ''),
                'published_at': comment.get('published_at', ''),
                'like_count': comment.get('like_count', 0),
                'reply_count': comment.get('reply_count', 0),
            }
            comments_data.append(comment_row)
    
    # Create DataFrames
    df_videos = pd.DataFrame(videos_data)
    df_comments = pd.DataFrame(comments_data)
    
    # Statistics
    print("=" * 80)
    print("VIDEO STATISTICS")
    print("=" * 80)
    print(f"Total Videos:         {len(videos_data)}")
    print(f"Total Views:          {df_videos['view_count'].sum():,}")
    print(f"Total Likes:          {df_videos['like_count'].sum():,}")
    print(f"Total Comments:       {df_videos['comment_count'].sum():,}")
    print(f"Avg Views/Video:      {df_videos['view_count'].mean():,.0f}")
    print(f"Avg Likes/Video:      {df_videos['like_count'].mean():,.0f}")
    print(f"Avg Comments/Video:   {df_videos['comment_count'].mean():,.0f}")
    print(f"Avg Engagement Rate:  {df_videos['engagement_rate'].mean():.2f}%")
    print()
    
    print("=" * 80)
    print("COMMENT STATISTICS")
    print("=" * 80)
    print(f"Total Comments:       {len(comments_data)}")
    if not df_comments.empty:
        print(f"Total Comment Likes:  {df_comments['like_count'].sum():,}")
        print(f"Total Replies:        {df_comments['reply_count'].sum():,}")
        print(f"Avg Likes/Comment:    {df_comments['like_count'].mean():.1f}")
    else:
        print("[INFO] No comments data available")
    print()
    
    # Top videos by views
    print("=" * 80)
    print("TOP 10 VIDEOS BY VIEWS")
    print("=" * 80)
    top_videos = df_videos.nlargest(10, 'view_count')
    print(f"{'Rank':<6} {'Views':>12} {'Likes':>10} {'Comments':>10} {'Eng.':>8}  {'Title':<50}")
    print("-" * 100)
    
    for i, (idx, video) in enumerate(top_videos.iterrows(), 1):
        title = video['title'][:47] + "..." if len(video['title']) > 50 else video['title']
        print(f"{i:<6} {video['view_count']:>12,} {video['like_count']:>10,} "
              f"{video['comment_count']:>10,} {video['engagement_rate']:>7.2f}%  {title}")
    print()
    
    # Generate output filename
    channel_id = channel_info.get('channel_id', 'unknown')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Export based on format
    output_dir = Path('data/export')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    files_created = []
    
    if output_format in ['excel', 'both']:
        excel_file = output_dir / f'youtube_{channel_id}_{timestamp}.xlsx'
        
        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
            # Channel Info sheet
            df_channel = pd.DataFrame([{
                'Channel ID': channel_info.get('channel_id', ''),
                'Channel Name': channel_info.get('title', ''),
                'Subscribers': channel_info.get('subscriber_count', 0),
                'Total Videos': channel_info.get('video_count', 0),
                'Total Views': channel_info.get('view_count', 0),
                'Published At': channel_info.get('published_at', ''),
                'Description': channel_info.get('description', '')[:500],
            }])
            df_channel.to_excel(writer, sheet_name='Channel Info', index=False)
            
            # Videos sheet
            df_videos.to_excel(writer, sheet_name='Videos', index=False)
            
            # Comments sheet
            if not df_comments.empty:
                df_comments.to_excel(writer, sheet_name='Comments', index=False)
            
            # Statistics sheet
            stats = {
                'Metric': [
                    'Total Videos',
                    'Total Views',
                    'Total Likes',
                    'Total Comments',
                    'Avg Views per Video',
                    'Avg Likes per Video',
                    'Avg Comments per Video',
                    'Avg Engagement Rate (%)',
                    'Total Comment Data',
                    'Total Comment Likes',
                ],
                'Value': [
                    len(videos_data),
                    df_videos['view_count'].sum(),
                    df_videos['like_count'].sum(),
                    df_videos['comment_count'].sum(),
                    df_videos['view_count'].mean(),
                    df_videos['like_count'].mean(),
                    df_videos['comment_count'].mean(),
                    df_videos['engagement_rate'].mean(),
                    len(comments_data),
                    df_comments['like_count'].sum() if not df_comments.empty else 0,
                ]
            }
            df_stats = pd.DataFrame(stats)
            df_stats.to_excel(writer, sheet_name='Statistics', index=False)
        
        files_created.append(str(excel_file))
        print(f"[OK] Excel file created: {excel_file}")
    
    if output_format in ['csv', 'both']:
        csv_videos = output_dir / f'youtube_{channel_id}_{timestamp}_videos.csv'
        df_videos.to_csv(csv_videos, index=False, encoding='utf-8-sig')
        files_created.append(str(csv_videos))
        print(f"[OK] Videos CSV created: {csv_videos}")
        
        if not df_comments.empty:
            csv_comments = output_dir / f'youtube_{channel_id}_{timestamp}_comments.csv'
            df_comments.to_csv(csv_comments, index=False, encoding='utf-8-sig')
            files_created.append(str(csv_comments))
            print(f"[OK] Comments CSV created: {csv_comments}")
    
    print()
    print("=" * 80)
    print("[COMPLETED] EXPORT FINISHED!")
    print("=" * 80)
    print()
    
    return files_created


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_youtube_data.py <json_file> [format]")
        print("  json_file: Path to YouTube JSON file")
        print("  format: 'excel', 'csv', or 'both' (default: excel)")
        print()
        print("Example:")
        print("  python export_youtube_data.py data/youtube_UCX6OQ3DkcsbYNE6H8uQQuVA_20260304_072401.json")
        print("  python export_youtube_data.py data/youtube_UCX6OQ3DkcsbYNE6H8uQQuVA_20260304_072401.json both")
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else 'excel'
    
    if not Path(json_file).exists():
        print(f"Error: File not found: {json_file}")
        sys.exit(1)
    
    export_youtube_data(json_file, output_format)
