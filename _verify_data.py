"""Verify all data numbers from the merged JSON for PPTX accuracy."""
import json
from collections import Counter
from datetime import datetime

DATA = 'data/merged/tiktok_travinhuniversity_merged.json'

with open(DATA, 'r', encoding='utf-8') as f:
    data = json.load(f)

videos = data if isinstance(data, list) else data.get('videos', data.get('data', []))
print(f"Total videos: {len(videos)}")

# Collect all comments
all_comments = []
for v in videos:
    comments = v.get('comments', [])
    all_comments.extend(comments)
print(f"Total comments: {len(all_comments)}")

# Stats
total_plays = 0
total_likes = 0
total_comments_count = 0  # from stats
total_shares = 0
total_saves = 0

for v in videos:
    stats = v.get('stats', v)
    total_plays += stats.get('play_count', stats.get('playCount', 0))
    total_likes += stats.get('like_count', stats.get('diggCount', 0))
    total_comments_count += stats.get('comment_count', stats.get('commentCount', 0))
    total_shares += stats.get('share_count', stats.get('shareCount', 0))
    total_saves += stats.get('collect_count', stats.get('collectCount', 0))

print(f"\n=== KPI (from video stats) ===")
print(f"Total Plays:    {total_plays:,}")
print(f"Total Likes:    {total_likes:,}")
print(f"Total Comments (TikTok stats): {total_comments_count:,}")
print(f"Total Shares:   {total_shares:,}")
print(f"Total Saves:    {total_saves:,}")
print(f"Comments collected (actual): {len(all_comments)}")

# Engagement
total_engagement = total_likes + total_comments_count + total_shares + total_saves
print(f"\nTotal engagement (L+C+S+Sv): {total_engagement:,}")

eng_rates = []
for v in videos:
    stats = v.get('stats', v)
    plays = stats.get('play_count', stats.get('playCount', 0))
    likes = stats.get('like_count', stats.get('diggCount', 0))
    cmt = stats.get('comment_count', stats.get('commentCount', 0))
    shares = stats.get('share_count', stats.get('shareCount', 0))
    saves = stats.get('collect_count', stats.get('collectCount', 0))
    if plays > 0:
        eng = (likes + cmt + shares + saves) / plays * 100
        eng_rates.append(eng)

avg_eng = sum(eng_rates) / len(eng_rates) if eng_rates else 0
like_rate = total_likes / total_plays * 100 if total_plays else 0
comment_rate = total_comments_count / total_plays * 100 if total_plays else 0
share_rate = total_shares / total_plays * 100 if total_plays else 0

print(f"\nAvg Engagement Rate: {avg_eng:.2f}%")
print(f"Like Rate: {like_rate:.2f}%")
print(f"Comment Rate: {comment_rate:.2f}%")
print(f"Share Rate: {share_rate:.2f}%")

# Sentiment
sentiments = Counter()
confidence_levels = {'high': 0, 'medium': 0, 'low': 0}
conf_by_sent = {}

for c in all_comments:
    sent = c.get('sentiment', 'unknown')
    conf = c.get('confidence', 0)
    sentiments[sent] += 1
    
    if sent not in conf_by_sent:
        conf_by_sent[sent] = []
    conf_by_sent[sent].append(conf)
    
    if conf >= 0.9:
        confidence_levels['high'] += 1
    elif conf >= 0.7:
        confidence_levels['medium'] += 1
    else:
        confidence_levels['low'] += 1

print(f"\n=== SENTIMENT ===")
total_c = len(all_comments)
for s in ['positive', 'neutral', 'negative']:
    cnt = sentiments.get(s, 0)
    pct = cnt / total_c * 100 if total_c else 0
    avg_conf = sum(conf_by_sent.get(s, [0])) / len(conf_by_sent.get(s, [1])) if conf_by_sent.get(s) else 0
    print(f"  {s}: {cnt} ({pct:.1f}%) avg_conf={avg_conf:.3f}")

print(f"\n=== CONFIDENCE ===")
for level, cnt in confidence_levels.items():
    pct = cnt / total_c * 100 if total_c else 0
    print(f"  {level}: {cnt} ({pct:.1f}%)")

# Top 10 videos by plays
print(f"\n=== TOP 10 VIDEOS BY PLAYS ===")
vids_sorted = sorted(videos, key=lambda v: v.get('stats', v).get('play_count', v.get('stats', v).get('playCount', 0)), reverse=True)
for i, v in enumerate(vids_sorted[:10]):
    stats = v.get('stats', v)
    vid = v.get('id', v.get('video_id', '?'))
    plays = stats.get('play_count', stats.get('playCount', 0))
    likes = stats.get('like_count', stats.get('diggCount', 0))
    cmt = stats.get('comment_count', stats.get('commentCount', 0))
    shares = stats.get('share_count', stats.get('shareCount', 0))
    saves = stats.get('collect_count', stats.get('collectCount', 0))
    eng = (likes + cmt + shares + saves) / plays * 100 if plays else 0
    print(f"  {i+1}. ID={vid}  plays={plays:,}  likes={likes:,}  cmt={cmt:,}  shares={shares:,}  saves={saves:,}  eng={eng:.2f}%")

# Top comments
print(f"\n=== TOP 5 POSITIVE COMMENTS (by likes) ===")
pos_comments = [c for c in all_comments if c.get('sentiment') == 'positive']
pos_sorted = sorted(pos_comments, key=lambda c: c.get('likes', 0), reverse=True)
for i, c in enumerate(pos_sorted[:5]):
    print(f"  {i+1}. likes={c.get('likes', 0):,}  conf={c.get('confidence', 0):.2f}  text={c.get('text', '')[:60]}")

print(f"\n=== TOP 5 NEGATIVE COMMENTS (by likes) ===")
neg_comments = [c for c in all_comments if c.get('sentiment') == 'negative']
neg_sorted = sorted(neg_comments, key=lambda c: c.get('likes', 0), reverse=True)
for i, c in enumerate(neg_sorted[:5]):
    print(f"  {i+1}. likes={c.get('likes', 0):,}  conf={c.get('confidence', 0):.2f}  text={c.get('text', '')[:60]}")

# Engagement donut data
print(f"\n=== ENGAGEMENT DONUT ===")
print(f"  Likes:    {total_likes:,}  ({total_likes/total_engagement*100:.1f}%)")
print(f"  Comments: {total_comments_count:,}  ({total_comments_count/total_engagement*100:.1f}%)")
print(f"  Shares:   {total_shares:,}  ({total_shares/total_engagement*100:.1f}%)")
print(f"  Saves:    {total_saves:,}  ({total_saves/total_engagement*100:.1f}%)")

# Engagement x Sentiment  
print(f"\n=== VIDEOS WITH BEST SENTIMENT SCORE ===")
video_sentiment = {}
for c in all_comments:
    vid = c.get('video_id', '')
    sent = c.get('sentiment', '')
    if vid not in video_sentiment:
        video_sentiment[vid] = {'positive': 0, 'neutral': 0, 'negative': 0}
    if sent in video_sentiment[vid]:
        video_sentiment[vid][sent] += 1

for v in videos:
    vid = str(v.get('id', ''))
    stats = v.get('stats', v)
    plays = stats.get('play_count', stats.get('playCount', 0))
    likes = stats.get('like_count', stats.get('diggCount', 0))
    cmt = stats.get('comment_count', stats.get('commentCount', 0))
    shares = stats.get('share_count', stats.get('shareCount', 0))
    saves = stats.get('collect_count', stats.get('collectCount', 0))
    eng = (likes + cmt + shares + saves) / plays * 100 if plays else 0
    
    if vid in video_sentiment:
        s = video_sentiment[vid]
        total_s = s['positive'] + s['neutral'] + s['negative']
        if total_s > 0:
            score = (s['positive'] - s['negative']) / total_s
            video_sentiment[vid]['eng'] = eng
            video_sentiment[vid]['plays'] = plays
            video_sentiment[vid]['score'] = score
            video_sentiment[vid]['vid'] = vid

# Best sentiment
scored = [(k, v) for k, v in video_sentiment.items() if 'score' in v and v.get('positive', 0) + v.get('negative', 0) > 0]
best = sorted(scored, key=lambda x: x[1]['score'], reverse=True)[:5]
print("  BEST (positive):")
for vid, s in best:
    print(f"    ID={vid}  plays={s['plays']:,}  eng={s['eng']:.2f}%  pos={s['positive']}  neg={s['negative']}  score={s['score']:.2f}")

worst = sorted(scored, key=lambda x: x[1]['score'])[:5]
print("  WORST (negative):")
for vid, s in worst:
    print(f"    ID={vid}  plays={s['plays']:,}  eng={s['eng']:.2f}%  pos={s['positive']}  neg={s['negative']}  score={s['score']:.2f}")
