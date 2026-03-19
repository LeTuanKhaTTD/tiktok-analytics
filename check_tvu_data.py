import json

# Load TVU data
with open('data/youtube_UCaxnllxL894OHbc_6VQcGmA_20260304_071941.json', encoding='utf-8') as f:
    data = json.load(f)

videos = data['videos']
channel_info = data['channel_info']

print("=" * 80)
print("TVU YOUTUBE DATA ANALYSIS")
print("=" * 80)
print()

print("CHANNEL INFO:")
print(f"  Total videos (channel): {channel_info['video_count']:,}")
print(f"  Total views (channel):  {channel_info['view_count']:,}")
print()

print("SCRAPED DATA:")
print(f"  Videos in JSON: {len(videos)}")
print()

print("DATE RANGE:")
dates = [v['published_at'] for v in videos]
print(f"  Oldest: {min(dates)}")
print(f"  Newest: {max(dates)}")
print()

print("VIEW STATISTICS:")
views = [v['view_count'] for v in videos]
print(f"  Total views (scraped): {sum(views):,}")
print(f"  Min views:  {min(views):,}")
print(f"  Max views:  {max(views):,}")
print(f"  Avg views:  {sum(views)/len(views):,.0f}")
print()

print("TOP 5 VIDEOS BY VIEWS:")
sorted_videos = sorted(videos, key=lambda x: x['view_count'], reverse=True)
for i, v in enumerate(sorted_videos[:5], 1):
    print(f"  {i}. {v['title'][:60]:60} - {v['view_count']:>6,} views ({v['published_at'][:10]})")
print()

print("BOTTOM 5 VIDEOS BY VIEWS:")
for i, v in enumerate(sorted_videos[-5:], 1):
    print(f"  {i}. {v['title'][:60]:60} - {v['view_count']:>6,} views ({v['published_at'][:10]})")
print()

# Compare with channel total
coverage = (sum(views) / channel_info['view_count']) * 100
print(f"DATA COVERAGE: {sum(views):,} / {channel_info['view_count']:,} = {coverage:.2f}%")
print(f"VIDEO COVERAGE: {len(videos)} / {channel_info['video_count']} = {(len(videos)/channel_info['video_count'])*100:.2f}%")
