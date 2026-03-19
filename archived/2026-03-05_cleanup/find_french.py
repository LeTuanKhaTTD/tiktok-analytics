import json

# Load data
with open('data/tong_hop_comment.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find French comments
all_comments = []
for video in data['videos']:
    for comment in video['comments']:
        comment['video_id'] = video['video_id']
        all_comments.append(comment)

# Search for French patterns
french_patterns = ['Faut', 'parce', 'arrêter', 'vouloir', "qu'", 'belle']
french_comments = []

for comment in all_comments:
    text = comment['text']
    if any(pattern in text for pattern in french_patterns):
        french_comments.append(comment)

print(f"Found {len(french_comments)} potential French comments")
print()

# Sort by likes
for c in sorted(french_comments, key=lambda x: x['likes'], reverse=True)[:5]:
    print(f"[{c['likes']:,} likes] Video: {c['video_id']}")
    print(f"  {c['text']}")
    print()
