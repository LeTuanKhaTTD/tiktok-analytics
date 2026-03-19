import json
from datetime import datetime

# Load data
print("Loading data...")
with open('data/tong_hop_comment.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find and remove French comment
total_before = 0
total_after = 0
removed_count = 0

for video in data['videos']:
    comments_before = len(video['comments'])
    total_before += comments_before
    
    # Filter out French comment
    filtered_comments = []
    for comment in video['comments']:
        text = comment['text']
        # Remove if contains French patterns
        if 'Faut arrêter' in text or ('parce' in text and "qu'elle" in text):
            print(f"\n🗑️  Removing French comment:")
            print(f"   Video: {video['video_id']}")
            print(f"   Likes: {comment['likes']:,}")
            print(f"   Text: {text[:100]}...")
            removed_count += 1
        else:
            filtered_comments.append(comment)
    
    # Update video
    video['comments'] = filtered_comments
    video['comments_count'] = len(filtered_comments)
    total_after += len(filtered_comments)

# Update global stats
data['total_comments'] = total_after
data['cleaned_at'] = datetime.now().isoformat()

print(f"\n📊 BEFORE: {total_before:,} comments")
print(f"📊 AFTER:  {total_after:,} comments")
print(f"🗑️  Removed: {removed_count} French comment(s)")

# Recalculate sentiment summary if exists
if 'global_sentiment_summary' in data:
    all_comments = []
    for video in data['videos']:
        all_comments.extend(video['comments'])
    
    positive = len([c for c in all_comments if c.get('sentiment') == 'positive'])
    negative = len([c for c in all_comments if c.get('sentiment') == 'negative'])
    neutral = len([c for c in all_comments if c.get('sentiment') == 'neutral'])
    
    data['global_sentiment_summary'] = {
        'positive': {
            'count': positive,
            'percentage': positive / total_after * 100 if total_after > 0 else 0
        },
        'negative': {
            'count': negative,
            'percentage': negative / total_after * 100 if total_after > 0 else 0
        },
        'neutral': {
            'count': neutral,
            'percentage': neutral / total_after * 100 if total_after > 0 else 0
        }
    }
    
    print(f"\n📊 Updated sentiment summary:")
    print(f"   ✅ Positive: {positive} ({positive/total_after*100:.1f}%)")
    print(f"   ❌ Negative: {negative} ({negative/total_after*100:.1f}%)")
    print(f"   ⚪ Neutral:  {neutral} ({neutral/total_after*100:.1f}%)")

# Save
output_file = 'data/tong_hop_comment.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n💾 Saved: {output_file}")
print("\n✅ Done! French comment removed.")
