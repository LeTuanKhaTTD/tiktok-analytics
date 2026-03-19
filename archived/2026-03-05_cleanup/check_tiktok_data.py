"""
Script kiểm tra số lượng video TikTok đã lấy được
"""
import json
import os
from pathlib import Path

def check_tiktok_data():
    """Kiểm tra tất cả file TikTok data"""
    
    print("="*80)
    print(" KIỂM TRA DỮ LIỆU TIKTOK")
    print("="*80)
    print()
    
    data_dir = Path("data")
    tiktok_files = []
    
    # Tìm tất cả file TikTok JSON
    for file in data_dir.glob("tiktok_travinhuniversity_*.json"):
        if "sentiment" not in file.name and "comprehensive" not in file.name:
            tiktok_files.append(file)
    
    if not tiktok_files:
        print("❌ Không tìm thấy file data TikTok nào!")
        return
    
    print(f"📂 Tìm thấy {len(tiktok_files)} file data TikTok:\n")
    
    total_videos = 0
    file_details = []
    
    for file in sorted(tiktok_files):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            videos = data.get('videos', [])
            username = data.get('username', 'N/A')
            
            # Lấy thông tin user
            user_info = data.get('user_info', {})
            stats = data.get('stats', {})
            
            file_details.append({
                'file': file.name,
                'username': username,
                'videos_count': len(videos),
                'followers': stats.get('follower_count', 0),
                'total_videos': stats.get('video_count', 0)
            })
            
            total_videos = max(total_videos, len(videos))
            
        except Exception as e:
            print(f"⚠️  Lỗi đọc file {file.name}: {e}")
    
    # In kết quả
    for detail in file_details:
        print(f"📄 {detail['file']}")
        print(f"   👤 Username: {detail['username']}")
        print(f"   📊 Videos đã lấy: {detail['videos_count']}")
        print(f"   👥 Followers: {detail['followers']:,}")
        print(f"   🎬 Tổng videos trên profile: {detail['total_videos']}")
        print()
    
    print("="*80)
    print(f" KẾT QUẢ TỔNG HỢP")
    print("="*80)
    print(f"✅ Số lượng video TikTok đã lấy: {total_videos}")
    print()
    
    # Kiểm tra file sentiment
    sentiment_files = list(data_dir.glob("*sentiment*.json"))
    if sentiment_files:
        print("💬 COMMENTS & SENTIMENT:")
        for sent_file in sentiment_files:
            try:
                with open(sent_file, 'r', encoding='utf-8') as f:
                    sent_data = json.load(f)
                total_comments = sent_data.get('total_comments', 0)
                print(f"   📄 {sent_file.name}")
                print(f"   💬 Comments: {total_comments}")
                
                sent_summary = sent_data.get('sentiment_summary', {})
                if sent_summary:
                    print(f"   ✅ Positive: {sent_summary.get('positive', {}).get('count', 0)}")
                    print(f"   ❌ Negative: {sent_summary.get('negative', {}).get('count', 0)}")
                    print(f"   ⚪ Neutral: {sent_summary.get('neutral', {}).get('count', 0)}")
                print()
            except:
                pass
    
    # Kiểm tra file comprehensive
    comp_files = list(data_dir.glob("*comprehensive*.json"))
    if comp_files:
        print("📊 COMPREHENSIVE ANALYSIS:")
        for comp_file in comp_files:
            print(f"   📄 {comp_file.name}")
        print()
    
    print("="*80)

if __name__ == "__main__":
    check_tiktok_data()
