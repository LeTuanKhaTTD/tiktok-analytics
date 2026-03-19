"""
TikTok Data Scraper Module
Thu thập dữ liệu từ TikTok API v2 (Content Posting API)

Note: TikTok API v2 yêu cầu OAuth 2.0 authentication
Xem thêm: https://developers.tiktok.com/doc/login-kit-web
"""

import requests
import time
import os
from typing import Dict, List, Optional
from datetime import datetime
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib
import base64
import secrets


class TikTokScraper:
    """
    Thu thập dữ liệu từ TikTok API v2
    
    Yêu cầu:
    - Client Key và Client Secret từ TikTok Developer Portal
    - Access Token (lấy thông qua OAuth 2.0)
    
    API Endpoints:
    - /v2/user/info/ - Thông tin user
    - /v2/video/list/ - Danh sách video
    - /v2/video/query/ - Chi tiết video
    - /v2/comment/list/ - Comments
    """
    
    def __init__(self, client_key: str, client_secret: str, access_token: str = None):
        """
        Khởi tạo TikTok Scraper
        
        Args:
            client_key: Client Key từ TikTok Developer
            client_secret: Client Secret từ TikTok Developer
            access_token: Access token (nếu đã có)
        """
        self.client_key = client_key
        self.client_secret = client_secret
        self.access_token = access_token
        
        # API Base URLs
        self.auth_url = "https://open.tiktokapis.com/v2/oauth/token/"
        self.api_base = "https://open.tiktokapis.com/v2"
        
        # PKCE parameters
        self.code_verifier = None
        self.code_challenge = None
        
        # Headers
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"
        
        # Setup session with retry logic
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Tạo session với retry logic"""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _generate_pkce_pair(self) -> tuple:
        """
        Tạo PKCE code verifier và code challenge
        
        Returns:
            Tuple (code_verifier, code_challenge)
        """
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
        code_verifier = code_verifier.replace('=', '')  # Remove padding
        
        # Generate code challenge (SHA256 hash of verifier)
        code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
        code_challenge = code_challenge.replace('=', '')  # Remove padding
        
        return code_verifier, code_challenge
    
    def get_authorization_url(self, redirect_uri: str, scope: str = None) -> str:
        """
        Tạo URL để user authorize (với PKCE support)
        
        Args:
            redirect_uri: URL callback sau khi user authorize
            scope: Permissions cần xin (mặc định: user.info.basic,video.list)
        
        Returns:
            URL để user click vào để authorize
        """
        if scope is None:
            scope = "user.info.basic,video.list"
        
        # Generate PKCE pair
        self.code_verifier, self.code_challenge = self._generate_pkce_pair()
        
        auth_url = (
            f"https://www.tiktok.com/v2/auth/authorize/"
            f"?client_key={self.client_key}"
            f"&scope={scope}"
            f"&response_type=code"
            f"&redirect_uri={redirect_uri}"
            f"&code_challenge={self.code_challenge}"
            f"&code_challenge_method=S256"
        )
        
        return auth_url
    
    def exchange_code_for_token(self, code: str, redirect_uri: str, code_verifier: str = None) -> Dict:
        """
        Đổi authorization code lấy access token
        
        Args:
            code: Authorization code từ callback
            redirect_uri: Redirect URI (phải giống lúc authorize)
            code_verifier: PKCE code verifier (nếu dùng PKCE)
        
        Returns:
            Dict chứa access_token, refresh_token, expires_in
        """
        # Use provided code_verifier or the one generated during get_authorization_url
        verifier = code_verifier or self.code_verifier
        
        payload = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        # Add code_verifier for PKCE
        if verifier:
            payload["code_verifier"] = verifier
        
        try:
            response = self.session.post(self.auth_url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("data"):
                token_data = data["data"]
                self.access_token = token_data.get("access_token")
                self.headers["Authorization"] = f"Bearer {self.access_token}"
                
                print(f" Đã lấy access token thành công!")
                print(f" Expires in: {token_data.get('expires_in')} seconds")
                
                return token_data
            else:
                error = data.get("error", {})
                raise Exception(f"Error: {error.get('code')} - {error.get('message')}")
                
        except Exception as e:
            print(f" Lỗi khi lấy access token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Làm mới access token khi hết hạn
        
        Args:
            refresh_token: Refresh token từ lần authorize trước
        
        Returns:
            Dict chứa access_token mới
        """
        payload = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        try:
            response = self.session.post(self.auth_url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("data"):
                token_data = data["data"]
                self.access_token = token_data.get("access_token")
                self.headers["Authorization"] = f"Bearer {self.access_token}"
                
                print(f" Đã refresh access token thành công!")
                return token_data
            else:
                error = data.get("error", {})
                raise Exception(f"Error: {error.get('code')} - {error.get('message')}")
                
        except Exception as e:
            print(f" Lỗi khi refresh token: {e}")
            return None
    
    def get_user_info(self) -> Dict:
        """
        Lấy thông tin user đang đăng nhập
        
        Returns:
            Dict chứa thông tin user: username, display_name, avatar_url, etc.
        """
        if not self.access_token:
            print(" Chưa có access token. Cần authorize trước.")
            return None
        
        url = f"{self.api_base}/user/info/"
        
        params = {
            "fields": "open_id,union_id,avatar_url,avatar_url_100,avatar_large_url,display_name,bio_description,profile_deep_link,is_verified,follower_count,following_count,likes_count,video_count"
        }
        
        try:
            response = self.session.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("data"):
                user_data = data["data"]["user"]
                print(f" Đã lấy thông tin user: {user_data.get('display_name')}")
                return user_data
            else:
                error = data.get("error", {})
                raise Exception(f"Error: {error.get('code')} - {error.get('message')}")
                
        except Exception as e:
            print(f" Lỗi khi lấy user info: {e}")
            return None
    
    def get_user_videos(self, max_videos: int = 20) -> List[Dict]:
        """
        Lấy danh sách video của user
        
        Args:
            max_videos: Số lượng video tối đa (mặc định: 20)
        
        Returns:
            List các video với metadata
        """
        if not self.access_token:
            print(" Chưa có access token. Cần authorize trước.")
            return []
        
        url = f"{self.api_base}/video/list/"
        
        params = {
            "fields": "id,create_time,cover_image_url,share_url,video_description,duration,height,width,title,embed_html,embed_link,like_count,comment_count,share_count,view_count"
        }
        
        all_videos = []
        cursor = None
        
        try:
            while len(all_videos) < max_videos:
                if cursor:
                    params["cursor"] = cursor
                
                params["max_count"] = min(20, max_videos - len(all_videos))
                
                response = self.session.post(url, headers=self.headers, json=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("data"):
                    videos = data["data"].get("videos", [])
                    all_videos.extend(videos)
                    
                    print(f"   Đã lấy {len(videos)} videos (tổng: {len(all_videos)})")
                    
                    # Check if has more
                    has_more = data["data"].get("has_more", False)
                    cursor = data["data"].get("cursor")
                    
                    if not has_more:
                        break
                else:
                    error = data.get("error", {})
                    print(f"  Error: {error.get('code')} - {error.get('message')}")
                    break
                
                time.sleep(0.5)  # Rate limit protection
            
            print(f" Đã lấy tổng cộng {len(all_videos)} videos")
            return all_videos[:max_videos]
            
        except Exception as e:
            print(f" Lỗi khi lấy videos: {e}")
            return all_videos
    
    def get_video_comments(self, video_id: str, max_comments: int = 50) -> List[Dict]:
        """
        Lấy comments của một video
        
        Args:
            video_id: ID của video
            max_comments: Số lượng comments tối đa (mặc định: 50)
        
        Returns:
            List các comments
        """
        if not self.access_token:
            print(" Chưa có access token. Cần authorize trước.")
            return []
        
        url = f"{self.api_base}/comment/list/"
        
        params = {
            "video_id": video_id,
            "fields": "id,video_id,text,like_count,reply_count,parent_comment_id,create_time"
        }
        
        all_comments = []
        cursor = None
        
        try:
            while len(all_comments) < max_comments:
                if cursor:
                    params["cursor"] = cursor
                
                params["max_count"] = min(50, max_comments - len(all_comments))
                
                response = self.session.post(url, headers=self.headers, json=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("data"):
                    comments = data["data"].get("comments", [])
                    all_comments.extend(comments)
                    
                    # Check if has more
                    has_more = data["data"].get("has_more", False)
                    cursor = data["data"].get("cursor")
                    
                    if not has_more:
                        break
                else:
                    error = data.get("error", {})
                    # Comment list có thể không available cho tất cả videos
                    if error.get("code") != "access_token_invalid":
                        print(f"  Video {video_id}: {error.get('message')}")
                    break
                
                time.sleep(0.3)  # Rate limit protection
            
            return all_comments[:max_comments]
            
        except Exception as e:
            print(f" Lỗi khi lấy comments: {e}")
            return all_comments
    
    def scrape_user_profile(self, max_videos: int = 20, max_comments_per_video: int = 50) -> Dict:
        """
        Thu thập toàn bộ dữ liệu của user profile
        
        Args:
            max_videos: Số lượng video tối đa
            max_comments_per_video: Số comments tối đa mỗi video
        
        Returns:
            Dict chứa user info, videos, và comments
        """
        print("="*80)
        print(" BẮT ĐẦU THU THẬP DỮ LIỆU TIKTOK")
        print("="*80)
        print()
        
        # 1. Get user info
        print("Bước 1: Lấy thông tin user...")
        user_info = self.get_user_info()
        
        if not user_info:
            print(" Không thể lấy thông tin user. Dừng lại.")
            return None
        
        print()
        
        # 2. Get videos
        print(f" Bước 2: Lấy danh sách videos (max: {max_videos})...")
        videos = self.get_user_videos(max_videos)
        
        if not videos:
            print("  Không có videos hoặc không thể truy cập.")
            return {
                "user_info": user_info,
                "videos": []
            }
        
        print()
        
        # 3. Get comments for each video
        print(f" Bước 3: Lấy comments cho {len(videos)} videos...")
        for i, video in enumerate(videos, 1):
            video_id = video.get("id")
            print(f"   Video {i}/{len(videos)}: {video_id}")
            
            comments = self.get_video_comments(video_id, max_comments_per_video)
            video["comments"] = comments
            
            print(f"      → Lấy được {len(comments)} comments")
        
        print()
        print("="*80)
        print(f" HOÀN TẤT! Đã thu thập {len(videos)} videos với {sum(len(v.get('comments', [])) for v in videos)} comments")
        print("="*80)
        print()
        
        return {
            "user_info": user_info,
            "videos": videos,
            "scraped_at": datetime.now().isoformat()
        }


def scrape_tiktok_user(client_key: str, client_secret: str, access_token: str,
                       max_videos: int = 20, max_comments_per_video: int = 50,
                       output_dir: str = 'data') -> Dict:
    """
    Helper function để thu thập dữ liệu TikTok
    
    Args:
        client_key: TikTok Client Key
        client_secret: TikTok Client Secret
        access_token: Access Token đã có
        max_videos: Số video tối đa
        max_comments_per_video: Số comments tối đa mỗi video
        output_dir: Thư mục lưu dữ liệu
    
    Returns:
        Dict chứa toàn bộ dữ liệu
    """
    scraper = TikTokScraper(client_key, client_secret, access_token)
    data = scraper.scrape_user_profile(max_videos, max_comments_per_video)
    
    if data and output_dir:
        # Save to file
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        username = data['user_info'].get('display_name', 'user').replace(' ', '_')
        filename = f"{output_dir}/tiktok_{username}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f" Đã lưu dữ liệu vào: {filename}")
    
    return data
