"""
YouTube Data Scraper
Module thu thập dữ liệu từ YouTube sử dụng YouTube Data API v3
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

#Class chính để thu thập dữ liệu từ YouTube
class YouTubeScraper:
    #Hàm khởi tạo với API key
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        
    #Hàm lấy thông tin channel    
    def get_channel_info(self, channel_id: str = None, channel_username: str = None) -> Optional[Dict]:
        try:
            if channel_id:
                request = self.youtube.channels().list(
                    part='snippet,statistics,contentDetails',
                    id=channel_id
                )
            elif channel_username:
                request = self.youtube.channels().list(
                    part='snippet,statistics,contentDetails',
                    forUsername=channel_username
                )
            else:
                print(" Lỗi: Cần cung cấp channel_id hoặc channel_username")
                return None
                
            response = request.execute()
            
            if not response.get('items'):
                print(" Không tìm thấy channel")
                return None
                
            channel = response['items'][0]
            
            return {
                'channel_id': channel['id'],
                'title': channel['snippet']['title'],
                'description': channel['snippet']['description'],
                'published_at': channel['snippet']['publishedAt'],
                'thumbnail': channel['snippet']['thumbnails']['high']['url'],
                'subscriber_count': int(channel['statistics'].get('subscriberCount', 0)),
                'video_count': int(channel['statistics'].get('videoCount', 0)),
                'view_count': int(channel['statistics'].get('viewCount', 0)),
                'uploads_playlist_id': channel['contentDetails']['relatedPlaylists']['uploads']
            }
            
        except HttpError as e:
            print(f" Lỗi HTTP: {e}")
            return None
        except Exception as e:
            print(f" Lỗi: {e}")
            return None
    
    #Hàm lấy danh sách videos từ channel
    def get_channel_videos(self, channel_id: str = None, channel_username: str = None, 
                          max_videos: int = 50) -> List[Dict]:
        try:
            # Lấy thông tin channel để có uploads playlist ID
            channel_info = self.get_channel_info(channel_id, channel_username)
            if not channel_info:
                return []
            
            uploads_playlist_id = channel_info['uploads_playlist_id']
            videos = []
            next_page_token = None
            
            while len(videos) < max_videos:
                # Lấy danh sách video IDs từ playlist
                request = self.youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_videos - len(videos)),
                    pageToken=next_page_token
                )
                
                response = request.execute()
                
                # Lấy video IDs
                video_ids = [item['contentDetails']['videoId'] for item in response.get('items', [])]
                
                if not video_ids:
                    break
                
                # Lấy thông tin chi tiết của videos
                videos_response = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(video_ids)
                ).execute()
                
                # Xử lý thông tin video
                for video in videos_response.get('items', []):
                    video_data = self._parse_video_data(video)
                    videos.append(video_data)
                
                # Kiểm tra có trang tiếp theo không
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            print(f" Đã lấy {len(videos)} videos từ channel")
            return videos[:max_videos]
            
        except HttpError as e:
            print(f" Lỗi HTTP: {e}")
            return []
        except Exception as e:
            print(f" Lỗi: {e}")
            return []
    
    def get_video_comments(self, video_id: str, max_comments: int = 100) -> List[Dict]:
        """
        Lấy comments từ một video
        
        Args:
            video_id: YouTube video ID
            max_comments: Số lượng comments tối đa cần lấy
            
        Returns:
            List các dictionary chứa thông tin comment
        """
        try:
            comments = []
            next_page_token = None
            
            while len(comments) < max_comments:
                request = self.youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=min(100, max_comments - len(comments)),
                    pageToken=next_page_token,
                    textFormat='plainText',
                    order='relevance'  # Lấy comments có relevance cao nhất
                )
                
                response = request.execute()
                
                for item in response.get('items', []):
                    comment = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'comment_id': item['snippet']['topLevelComment']['id'],
                        'author': comment['authorDisplayName'],
                        'text': comment['textDisplay'],
                        'published_at': comment['publishedAt'],
                        'like_count': comment['likeCount'],
                        'reply_count': item['snippet']['totalReplyCount']
                    })
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return comments[:max_comments]
            
        except HttpError as e:
            if e.resp.status == 403:
                print(f"Comments bị tắt cho video {video_id}")
            else:
                print(f" Lỗi HTTP khi lấy comments: {e}")
            return []
        except Exception as e:
            print(f"Lỗi khi lấy comments: {e}")
            return []
    
    #Hàm xử lý dữ liệu video trả về từ API
    def _parse_video_data(self, video: Dict) -> Dict:
        snippet = video['snippet']
        statistics = video.get('statistics', {})
        
        return {
            'video_id': video['id'],
            'title': snippet['title'],
            'description': snippet['description'],
            'published_at': snippet['publishedAt'],
            'channel_title': snippet['channelTitle'],
            'thumbnail': snippet['thumbnails']['high']['url'],
            'tags': snippet.get('tags', []),
            'category_id': snippet.get('categoryId'),
            'duration': video['contentDetails']['duration'],
            'view_count': int(statistics.get('viewCount', 0)),
            'like_count': int(statistics.get('likeCount', 0)),
            'comment_count': int(statistics.get('commentCount', 0)),
            'favorite_count': int(statistics.get('favoriteCount', 0))
        }
    
    #Hàm lưu dữ liệu vào file JSON
    def save_to_json(self, data: Dict, filename: str, output_dir: str = 'data'):
        """
        Lưu dữ liệu vào file JSON
        
        Args:
            data: Dữ liệu cần lưu
            filename: Tên file
            output_dir: Thư mục đầu ra
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"Đã lưu dữ liệu vào {filepath}")
            
        except Exception as e:
            print(f"Lỗi khi lưu file: {e}")

#Hàm tiện ích để scrape toàn bộ dữ liệu từ một YouTube channel
def scrape_youtube_channel(channel_id: str = None, channel_username: str = None,
                           api_key: str = None, max_videos: int = 30, 
                           max_comments_per_video: int = 50,
                           output_dir: str = 'data') -> Optional[Dict]:
    if not api_key:
        print("Lỗi: Cần cung cấp YouTube API key")
        return None
    
    if not channel_id and not channel_username:
        print("Lỗi: Cần cung cấp channel_id hoặc channel_username")
        return None
    
    scraper = YouTubeScraper(api_key)
    
    # Lấy thông tin channel
    print(f"\nĐang lấy thông tin channel...")
    channel_info = scraper.get_channel_info(channel_id, channel_username)
    if not channel_info:
        return None
    
    print(f" Channel: {channel_info['title']}")
    print(f"   Subscribers: {channel_info['subscriber_count']:,}")
    print(f"   Total Videos: {channel_info['video_count']:,}")
    print(f"   Total Views: {channel_info['view_count']:,}")
    
    # Lấy danh sách videos
    print(f"\nĐang lấy {max_videos} videos gần nhất...")
    videos = scraper.get_channel_videos(
        channel_id=channel_info['channel_id'],
        max_videos=max_videos
    )
    
    if not videos:
        print("Không thể lấy videos")
        return None
    
    # Lấy comments cho mỗi video
    print(f"\nĐang lấy comments cho {len(videos)} videos...")
    for i, video in enumerate(videos, 1):
        print(f"   [{i}/{len(videos)}] {video['title'][:50]}...")
        comments = scraper.get_video_comments(
            video['video_id'],
            max_comments=max_comments_per_video
        )
        video['comments'] = comments
        video['comments_count'] = len(comments)
    
    # Tổng hợp dữ liệu
    result = {
        'channel_info': channel_info,
        'videos': videos,
        'total_videos': len(videos),
        'total_comments': sum(len(v['comments']) for v in videos),
        'scraped_at': datetime.now().isoformat()
    }
    
    # Lưu dữ liệu
    identifier = channel_username or channel_id
    filename = f"youtube_{identifier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    scraper.save_to_json(result, filename, output_dir)
    
    print(f"\nHoàn thành thu thập dữ liệu!")
    print(f"Tổng số videos: {len(videos)}")
    print(f"Tổng số comments: {result['total_comments']}")
    
    return result
