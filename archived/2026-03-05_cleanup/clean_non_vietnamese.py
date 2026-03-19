"""
Clean Non-Vietnamese Comments - Lọc bỏ comments không phải tiếng Việt
"""
import json
import re
from datetime import datetime
from langdetect import detect, LangDetectException

def is_vietnamese(text):
    """
    Kiểm tra xem text có phải tiếng Việt không
    """
    if not text or len(text.strip()) < 3:
        return False
    
    # Vietnamese diacritics
    vietnamese_chars = ['ă', 'â', 'đ', 'ê', 'ô', 'ơ', 'ư',
                       'à', 'á', 'ả', 'ã', 'ạ',
                       'ằ', 'ắ', 'ẳ', 'ẵ', 'ặ',
                       'ầ', 'ấ', 'ẩ', 'ẫ', 'ậ',
                       'è', 'é', 'ẻ', 'ẽ', 'ẹ',
                       'ề', 'ế', 'ể', 'ễ', 'ệ',
                       'ì', 'í', 'ỉ', 'ĩ', 'ị',
                       'ò', 'ó', 'ỏ', 'õ', 'ọ',
                       'ồ', 'ố', 'ổ', 'ỗ', 'ộ',
                       'ờ', 'ớ', 'ở', 'ỡ', 'ợ',
                       'ù', 'ú', 'ủ', 'ũ', 'ụ',
                       'ừ', 'ứ', 'ử', 'ữ', 'ự',
                       'ỳ', 'ý', 'ỷ', 'ỹ', 'ỵ']
    
    text_lower = text.lower()
    
    # Check for Vietnamese diacritics
    has_vietnamese_chars = any(char in text_lower for char in vietnamese_chars)
    
    if has_vietnamese_chars:
        return True
    
    # Try language detection as backup
    try:
        lang = detect(text)
        return lang == 'vi'
    except LangDetectException:
        # If can't detect, check for common Vietnamese words without diacritics
        common_vi_words = ['cho', 'cua', 'nha', 'thi', 'con', 'nay', 'ban', 
                          'toi', 'voi', 'hay', 'lam', 'den', 'khong', 'duoc']
        words = text_lower.split()
        vi_word_count = sum(1 for word in words if word in common_vi_words)
        
        # If more than 20% are common Vietnamese words
        if len(words) > 0 and (vi_word_count / len(words)) > 0.2:
            return True
    
    return False

def is_french(text):
    """
    Kiểm tra xem text có phải tiếng Pháp không
    """
    french_patterns = [
        r"\bqu['']",  # qu'
        r"\bc['']est\b",  # c'est
        r"\bd['']",  # d'
        r'\bparce\s+qu',  # parce que
        r'\bavec\b',
        r'\belle\b',
        r'\bfaut\b',
        r'\bvouloir\b',
        r'\barrêter\b',
        r'\bfaisant\b'
    ]
    
    for pattern in french_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def clean_comments(input_file):
    """
    Lọc bỏ comments không phải tiếng Việt
    """
    print("="*80)
    print(" LỌC COMMENTS TIẾNG VIỆT - CLEAN NON-VIETNAMESE COMMENTS")
    print("="*80)
    print()
    
    # Load data
    print(f"📂 Loading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_videos = len(data.get('videos', []))
    total_comments_before = 0
    
    # Count total comments
    for video in data['videos']:
        total_comments_before += len(video.get('comments', []))
    
    print(f"   📊 Before: {total_comments_before:,} comments from {total_videos} videos")
    print()
    
    # Track removed comments
    removed_comments = []
    french_comments = []
    other_language_comments = []
    
    # Clean each video
    cleaned_videos = []
    total_comments_after = 0
    
    print("🔍 Analyzing comments...")
    print()
    
    for video in data['videos']:
        video_id = video.get('video_id')
        comments = video.get('comments', [])
        
        cleaned_comments = []
        
        for comment in comments:
            text = comment.get('text', '')
            
            # Check if Vietnamese
            if is_vietnamese(text):
                cleaned_comments.append(comment)
            else:
                # Not Vietnamese - check why
                removed_comments.append({
                    'text': text,
                    'likes': comment.get('likes', 0),
                    'video_id': video_id,
                    'reason': 'non-vietnamese'
                })
                
                if is_french(text):
                    french_comments.append({
                        'text': text,
                        'likes': comment.get('likes', 0),
                        'video_id': video_id
                    })
                else:
                    other_language_comments.append({
                        'text': text,
                        'likes': comment.get('likes', 0),
                        'video_id': video_id
                    })
        
        # Update video with cleaned comments
        if cleaned_comments:  # Only keep videos with Vietnamese comments
            video['comments'] = cleaned_comments
            video['comments_count'] = len(cleaned_comments)
            video['total_likes'] = sum(c.get('likes', 0) for c in cleaned_comments)
            video['avg_likes_per_comment'] = video['total_likes'] / len(cleaned_comments) if cleaned_comments else 0
            
            cleaned_videos.append(video)
            total_comments_after += len(cleaned_comments)
    
    # Update global stats
    data['videos'] = cleaned_videos
    data['total_videos'] = len(cleaned_videos)
    data['total_comments'] = total_comments_after
    data['total_likes'] = sum(v.get('total_likes', 0) for v in cleaned_videos)
    data['cleaned_at'] = datetime.now().isoformat()
    
    print("="*80)
    print(" KẾT QUẢ LỌC")
    print("="*80)
    print()
    print(f"📊 BEFORE: {total_comments_before:,} comments from {total_videos} videos")
    print(f"📊 AFTER:  {total_comments_after:,} comments from {len(cleaned_videos)} videos")
    print()
    print(f"🗑️  Removed: {len(removed_comments):,} comments ({len(removed_comments)/total_comments_before*100:.1f}%)")
    print()
    
    if french_comments:
        print(f"🇫🇷 French comments removed: {len(french_comments)}")
        print("-" * 80)
        for idx, comment in enumerate(sorted(french_comments, key=lambda x: x['likes'], reverse=True)[:5], 1):
            print(f"{idx}. [{comment['likes']:,} likes] Video: {comment['video_id']}")
            print(f"   \"{comment['text'][:80]}...\"")
        print()
    
    if other_language_comments:
        print(f"🌍 Other language comments removed: {len(other_language_comments)}")
        print("-" * 80)
        for idx, comment in enumerate(sorted(other_language_comments, key=lambda x: x['likes'], reverse=True)[:5], 1):
            print(f"{idx}. [{comment['likes']:,} likes] Video: {comment['video_id']}")
            print(f"   \"{comment['text'][:80]}...\"")
        print()
    
    # Save cleaned data
    output_file = input_file.replace('.json', '_cleaned.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved cleaned data: {output_file}")
    print()
    
    # Save removed comments for review
    removed_file = input_file.replace('.json', '_removed_comments.json')
    removed_data = {
        'total_removed': len(removed_comments),
        'french_comments': french_comments,
        'other_language_comments': other_language_comments,
        'removed_at': datetime.now().isoformat()
    }
    
    with open(removed_file, 'w', encoding='utf-8') as f:
        json.dump(removed_data, f, indent=2, ensure_ascii=False)
    
    print(f"📋 Saved removed comments: {removed_file}")
    print()
    
    print("="*80)
    print(" ✅ COMPLETED!")
    print("="*80)
    print()
    print("Next steps:")
    print(f"1. Review removed comments: {removed_file}")
    print(f"2. Run sentiment analysis on cleaned data:")
    print(f"   python run_sentiment_analysis_phobert.py {output_file}")
    print()
    
    return output_file

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "data/tong_hop_comment.json"
    
    clean_comments(input_file)
