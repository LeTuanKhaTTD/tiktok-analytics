"""
TikTok API Scraper - Unofficial API
Lấy được DATA THẬT: videos, likes, comments, shares, views
Không cần approval, không cần OAuth
"""
from TikTokApi import TikTokApi
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List

class TikTokAPICollector:
    """Thu thập TikTok data qua Unofficial API"""
    
    def __init__(self):
        self.api = None
    
    @staticmethod
    def _to_int(value) -> int:
        """Convert value to int safely"""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            return int(value) if value.isdigit() else 0
        return 0
    
    async def get_user_data(self, username: str, max_videos: int = 30) -> Dict:
        """
        Lấy data của user TikTok
        Args:
            username: TikTok username (có hoặc không có @), hoặc URL đầy đủ
            max_videos: Số videos tối đa cần lấy
        Returns:
            Dict chứa user info và videos với FULL metrics
        """
        # Parse username từ URL nếu cần
        if 'tiktok.com' in username:

            # Extract username from URL: https://www.tiktok.com/@username
            parts = username.split('@')
            if len(parts) > 1:
                username = parts[-1].split('/')[0].split('?')[0]
            else:

            # URL không có @ (ví dụ: tiktok.com/username)
                username = username.split('/')[-1].split('?')[0]

            # Remove @ if present
        username = username.replace('@', '').strip()
        print(f" Đang thu thập data từ TikTok: @{username}")
        print(f" Đang khởi động browser...")
        print(f" ℹ️  Browser sẽ mở, ĐỪNG ĐÓNG cho đến khi hoàn tất!")
        print()
        
        # Cấu hình context options để giảm bot detection
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "locale": "vi-VN",
            "timezone_id": "Asia/Ho_Chi_Minh",
        }
        
        # Sử dụng headless=False bắt buộc để bypass bot detection
        async with TikTokApi() as api:
            try:
                # Config với stealth settings mạnh hơn
                await api.create_sessions(
                    ms_tokens=[None],  
                    num_sessions=1, 
                    sleep_after=5,  # Tăng delay từ 3 lên 5 seconds
                    headless=False,  # MUST BE FALSE
                    context_options=context_options,
                    override_browser_args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-web-security",
                        "--disable-features=IsolateOrigins,site-per-process",
                        "--lang=vi-VN",
                    ]
                )
                print(f" ✅ Browser đã sẵn sàng!")
                # Đợi thêm 3 giây sau khi khởi tạo
                await asyncio.sleep(3)
            except Exception as e:
                print(f" ❌ Lỗi: {e}")
                print(f" 💡 Có thể TikTok đang chặn kết nối từ region của bạn")
                print(f" 💡 Thử: 1) Dùng VPN, 2) Đợi 10-15 phút, 3) Thử account khác")
                return None
            
            # Lấy user info
            try:
                user = api.user(username)
                user_data = await user.info()
                
                print(f"   Tìm thấy user: {user_data['userInfo']['user']['nickname']}")
                print(f"   Followers: {user_data['userInfo']['stats']['followerCount']:,}")
                print(f"   Videos: {user_data['userInfo']['stats']['videoCount']:,}")
                
                # Lấy videos
                print(f" Đang lấy {max_videos} videos gần nhất...")
                videos = []
                video_count = 0
                
                async for video in user.videos(count=max_videos):
                    video_count += 1
                    
                    # Extract stats safely
                    stats = video.stats if hasattr(video, 'stats') else {}
                    play_count = self._to_int(stats.get('playCount', 0))
                    like_count = self._to_int(stats.get('diggCount', 0))
                    comment_count = self._to_int(stats.get('commentCount', 0))
                    share_count = self._to_int(stats.get('shareCount', 0))
                    download_count = self._to_int(stats.get('downloadCount', 0))
                    
                    video_info = {
                        'id': video.id,
                        'desc': video.desc if hasattr(video, 'desc') else '',
                        'create_time': video.create_time if hasattr(video, 'create_time') else 0,
                        'video_url': f"https://www.tiktok.com/@{username}/video/{video.id}",
                        
                        # METRICS QUAN TRỌNG
                        'stats': {
                            'play_count': play_count,
                            'like_count': like_count,
                            'comment_count': comment_count,
                            'share_count': share_count,
                            'download_count': download_count
                        },
                        
                        # Tính engagement rate
                        'engagement_rate': self._calculate_engagement(video.stats if hasattr(video, 'stats') else {}),
                        
                        # Video details
                        'duration': video.video.get('duration', 0) if hasattr(video, 'video') else 0,
                        'music': {
                            'title': video.music.get('title', '') if hasattr(video, 'music') else '',
                            'author': video.music.get('authorName', '') if hasattr(video, 'music') else ''
                        },
                        'hashtags': [tag.get('name', '') for tag in (video.challenges if hasattr(video, 'challenges') else [])]
                    }
                    
                    videos.append(video_info)
                    
                    stats = video_info['stats']
                    print(f"   [{video_count}/{max_videos}] Video {video.id}: {stats['play_count']:,} views, {stats['like_count']:,} likes")
                
                # Lấy comments của top videos
                print(f" Đang lấy comments...")
                for i, video in enumerate(videos[:5], 1):  # Lấy comments của top 5 videos
                    print(f"   [{i}/5] Lấy comments của video {video['id']}...")
                    comments = await self._get_video_comments(api, video['id'], username, max_comments=50)
                    video['comments'] = comments
                    print(f"       → {len(comments)} comments")
                
                # Tổng hợp data
                result = {
                    'username': f"@{username}",
                    'user_info': {
                        'id': user_data['userInfo']['user']['id'],
                        'nickname': user_data['userInfo']['user']['nickname'],
                        'signature': user_data['userInfo']['user'].get('signature', ''),
                        'avatar': user_data['userInfo']['user'].get('avatarLarger', ''),
                        'verified': user_data['userInfo']['user'].get('verified', False),
                    },
                    'stats': {
                        'follower_count': user_data['userInfo']['stats']['followerCount'],
                        'following_count': user_data['userInfo']['stats']['followingCount'],
                        'heart_count': user_data['userInfo']['stats']['heartCount'],
                        'video_count': user_data['userInfo']['stats']['videoCount'],
                    },
                    'videos': videos,
                    'total_videos_analyzed': len(videos),
                    'collected_at': datetime.now().isoformat(),
                    
                    # Tính toán metrics tổng hợp
                    'aggregated_metrics': self._calculate_aggregated_metrics(videos, user_data['userInfo']['stats'])
                }
                
                print(f"\n Hoàn tất thu thập data!")
                print(f"   Total videos: {len(videos)}")
                print(f"   Total views: {sum(v['stats']['play_count'] for v in videos):,}")
                print(f"   Total likes: {sum(v['stats']['like_count'] for v in videos):,}")
                print(f"   Total comments: {sum(v['stats']['comment_count'] for v in videos):,}")
                
                return result
                
            except Exception as e:
                print(f" Lỗi: {e}")
                import traceback
                traceback.print_exc()
                return None
    
    async def get_user_data_with_cookie(self, username: str, max_videos: int = 30, ms_token: str = None) -> Dict:
        """
        Lấy data của user TikTok với manual cookie (ms_token từ browser thật)
        Bypass bot detection hoàn toàn
        
        Args:
            username: TikTok username
            max_videos: Số videos tối đa
            ms_token: Cookie ms_token lấy từ browser (xem get_tiktok_cookie.py)
        
        Returns:
            Dict chứa formatted data + save_path + index_id
        """
        from utils.file_manager import DataManager
        from utils.index_manager import IndexManager
        
        # Parse username
        if 'tiktok.com' in username:
            parts = username.split('@')
            if len(parts) > 1:
                username = parts[-1].split('/')[0].split('?')[0]
            else:
                username = username.split('/')[-1].split('?')[0]
        username = username.replace('@', '').strip()
        
        print(f" Đang thu thập data từ TikTok: @{username}")
        print(f" Đang khởi động browser với MANUAL COOKIE...")
        print(f" ℹ️  Browser sẽ mở với session đã authenticated!")
        print()
        
        # Context options giống như trước
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "locale": "vi-VN",
            "timezone_id": "Asia/Ho_Chi_Minh",
        }
        
        async with TikTokApi() as api:
            try:
                # Sử dụng ms_token thật từ browser
                await api.create_sessions(
                    ms_tokens=[ms_token] if ms_token else [None],
                    num_sessions=1,
                    sleep_after=3,
                    headless=False,
                    context_options=context_options,
                    override_browser_args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                    ]
                )
                print(f" ✅ Browser đã authenticated với cookie!")
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f" ❌ Lỗi: {e}")
                return {'error': str(e)}
            
            # Lấy user info
            try:
                user = api.user(username)
                user_data = await user.info()
                
                print(f"   Tìm thấy user: {user_data['userInfo']['user']['nickname']}")
                print(f"   Followers: {user_data['userInfo']['stats']['followerCount']:,}")
                print(f"   Videos: {user_data['userInfo']['stats']['videoCount']:,}")
                
                # Lấy videos (logic giống như trước)
                print(f" Đang lấy {max_videos} videos gần nhất...")
                videos = []
                video_count = 0
                
                async for video in user.videos(count=max_videos):
                    video_count += 1
                    stats = video.stats if hasattr(video, 'stats') else {}
                    play_count = self._to_int(stats.get('playCount', 0))
                    like_count = self._to_int(stats.get('diggCount', 0))
                    comment_count = self._to_int(stats.get('commentCount', 0))
                    share_count = self._to_int(stats.get('shareCount', 0))
                    
                    video_info = {
                        'id': video.id,
                        'desc': video.desc if hasattr(video, 'desc') else '',
                        'create_time': video.create_time if hasattr(video, 'create_time') else 0,
                        'stats': {
                            'play_count': play_count,
                            'like_count': like_count,
                            'comment_count': comment_count,
                            'share_count': share_count,
                        },
                        'engagement_rate': self._calculate_engagement(stats),
                        'comments': []
                    }
                    videos.append(video_info)
                    print(f"   [{video_count}/{max_videos}] {video.id} - {play_count:,} views")
                
                # Lấy comments
                print(f" Đang lấy comments...")
                for i, video in enumerate(videos[:5], 1):
                    print(f"   [{i}/5] Lấy comments của video {video['id']}...")
                    comments = await self._get_video_comments(api, video['id'], username, max_comments=50)
                    video['comments'] = comments
                    print(f"       → {len(comments)} comments")
                
                # Format data
                formatted_data = {
                    'username': f"@{username}",
                    'user_info': {
                        'unique_id': username,
                        'nickname': user_data['userInfo']['user']['nickname'],
                        'signature': user_data['userInfo']['user'].get('signature', ''),
                        'avatar': user_data['userInfo']['user'].get('avatarLarger', ''),
                        'verified': user_data['userInfo']['user'].get('verified', False),
                        'follower_count': user_data['userInfo']['stats']['followerCount'],
                        'following_count': user_data['userInfo']['stats']['followingCount'],
                        'video_count': user_data['userInfo']['stats']['videoCount'],
                    },
                    'videos': videos,
                    'total_videos_analyzed': len(videos),
                    'collected_at': datetime.now().isoformat(),
                }
                
                # Flatten video stats for easier access
                for video in formatted_data['videos']:
                    video.update({
                        'play_count': video['stats']['play_count'],
                        'like_count': video['stats']['like_count'],
                        'comment_count': video['stats']['comment_count'],
                        'share_count': video['stats']['share_count'],
                    })
                
                # Lưu với DataManager
                dm = DataManager()
                save_path = dm.get_save_path('tiktok', username)
                os.makedirs(save_path, exist_ok=True)
                
                raw_file = os.path.join(save_path, 'raw_data.json')
                with open(raw_file, 'w', encoding='utf-8') as f:
                    json.dump(formatted_data, f, indent=2, ensure_ascii=False)
                
                # Index
                im = IndexManager()
                index_id = im.add_analysis(
                    platform='tiktok',
                    account_id=username,
                    data_path=save_path,
                    metrics={
                        'videos': len(videos),
                        'total_views': sum(v['play_count'] for v in videos),
                        'total_likes': sum(v['like_count'] for v in videos),
                        'avg_engagement': sum(v['engagement_rate'] for v in videos) / len(videos) if videos else 0
                    }
                )
                
                formatted_data['save_path'] = raw_file
                formatted_data['index_id'] = f"#{index_id}"
                
                print(f"\n Hoàn tất thu thập data!")
                print(f"   Total videos: {len(videos)}")
                print(f"   Total views: {sum(v['play_count'] for v in videos):,}")
                print(f"   Total likes: {sum(v['like_count'] for v in videos):,}")
                
                return formatted_data
                
            except Exception as e:
                print(f" Lỗi: {e}")
                import traceback
                traceback.print_exc()
                return {'error': str(e)}
    
    async def _get_video_comments(self, api, video_id: str, username: str, max_comments: int = 50) -> List[Dict]:
        """Lấy comments của video"""
        try:
            video = api.video(id=video_id)
            comments = []
            count = 0
            
            async for comment in video.comments(count=max_comments):
                try:
                    comments.append({
                        'text': comment.text if hasattr(comment, 'text') else '',
                        'author': comment.user.username if hasattr(comment, 'user') and hasattr(comment.user, 'username') else 'unknown',
                        'likes': comment.likes_count if hasattr(comment, 'likes_count') else 0,
                        'create_time': comment.create_time if hasattr(comment, 'create_time') else 0
                    })
                    count += 1
                    if count >= max_comments:
                        break
                except:
                    continue
            
            return comments
        except Exception as e:
            print(f"     Không thể lấy comments: {e}")
            return []
    
    def _calculate_engagement(self, stats: Dict) -> float:
        """Tính engagement rate"""
        plays = stats.get('playCount', 0)
        if plays == 0:
            return 0.0
        
        # Convert to int if string
        if isinstance(plays, str):
            plays = int(plays) if plays.isdigit() else 0
        
        likes = stats.get('diggCount', 0)
        comments = stats.get('commentCount', 0)
        shares = stats.get('shareCount', 0)
        
        # Convert all to int
        if isinstance(likes, str):
            likes = int(likes) if likes.isdigit() else 0
        if isinstance(comments, str):
            comments = int(comments) if comments.isdigit() else 0
        if isinstance(shares, str):
            shares = int(shares) if shares.isdigit() else 0
        
        engagement = likes + comments + shares
        
        if plays == 0:
            return 0.0
            
        return (engagement / plays) * 100
    
    def _calculate_aggregated_metrics(self, videos: List[Dict], user_stats: Dict) -> Dict:
        """Tính metrics tổng hợp"""
        if not videos:
            return {}
        
        total_views = sum(v['stats']['play_count'] for v in videos)
        total_likes = sum(v['stats']['like_count'] for v in videos)
        total_comments = sum(v['stats']['comment_count'] for v in videos)
        total_shares = sum(v['stats']['share_count'] for v in videos)
        
        return {
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'avg_views_per_video': total_views / len(videos) if videos else 0,
            'avg_likes_per_video': total_likes / len(videos) if videos else 0,
            'avg_engagement_rate': sum(v['engagement_rate'] for v in videos) / len(videos) if videos else 0,
            'total_engagement': total_likes + total_comments + total_shares,
            'engagement_rate': ((total_likes + total_comments + total_shares) / total_views * 100) if total_views > 0 else 0,
            
            # Virality metrics
            'virality_score': self._calculate_virality_score(videos),
            'best_performing_video': max(videos, key=lambda x: x['stats']['play_count']) if videos else None
        }
    
    def _calculate_virality_score(self, videos: List[Dict]) -> float:
        """Tính virality score (0-100)"""
        if not videos:
            return 0.0
        
        # Dựa trên shares và engagement
        total_shares = sum(v['stats']['share_count'] for v in videos)
        total_views = sum(v['stats']['play_count'] for v in videos)
        
        if total_views == 0:
            return 0.0
        
        share_rate = (total_shares / total_views) * 100
        avg_engagement = sum(v['engagement_rate'] for v in videos) / len(videos)
        
        # Normalize về 0-100
        virality = (share_rate * 0.6 + avg_engagement * 0.4)
        return min(virality * 10, 100)  # Scale up
    
    def save_data(self, data: Dict, output_dir: str = 'data') -> str:
        """Lưu data vào file"""
        os.makedirs(output_dir, exist_ok=True)
        
        username = data['username'].replace('@', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'tiktok_{username}_{timestamp}.json'
        filepath = os.path.join(output_dir, filename)
        
        # Convert datetime to string for JSON serialization
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=convert_datetime)
        
        print(f" Đã lưu data: {filepath}")
        return filepath


async def collect_tiktok_data(username: str, max_videos: int = 30, output_dir: str = 'data') -> Dict:
    """
    Helper function để thu thập TikTok data
    
    Args:
        username: TikTok username
        max_videos: Số videos cần lấy
        output_dir: Thư mục lưu data
    
    Returns:
        Dict chứa full TikTok data
    """
    collector = TikTokAPICollector()
    data = await collector.get_user_data(username, max_videos)
    
    if data:
        collector.save_data(data, output_dir)
    
    return data


# Test script
if __name__ == '__main__':
    import sys
    
    username = input("Nhập TikTok username, @username, hoặc URL (ví dụ: khaby.lame, @khaby.lame, https://www.tiktok.com/@khaby.lame): ").strip()
    
    if not username:
        print(" Username không được để trống!")
        sys.exit(1)
    
    print("="*80)
    print(" TIKTOK DATA COLLECTOR")
    print("="*80)
    print()
    
    data = asyncio.run(collect_tiktok_data(username, max_videos=20))
    
    if data:
        print("\n" + "="*80)
        print(" TỔNG KẾT DATA")
        print("="*80)
        metrics = data['aggregated_metrics']
        print(f" User: {data['username']}")
        print(f"   Nickname: {data['user_info']['nickname']}")
        print(f"   Followers: {data['stats']['follower_count']:,}")
        print(f" Total Views: {metrics['total_views']:,}")
        print(f"  Total Likes: {metrics['total_likes']:,}")
        print(f" Total Comments: {metrics['total_comments']:,}")
        print(f" Total Shares: {metrics['total_shares']:,}")
        print(f" Avg Engagement Rate: {metrics['avg_engagement_rate']:.2f}%")
        print(f" Virality Score: {metrics['virality_score']:.2f}/100")
        print()
        print(" Data đã được lưu vào thư mục data/")
    else:
        print("\n Không thể thu thập data!")
        sys.exit(1)
