"""
HƯỚNG DẪN: TỰ ĐỘNG LẤY COMMENTS TIKTOK VỚI PLAYWRIGHT
=====================================================

## YÊU CẦU:
- ⚠️ Chỉ dùng cho NGHIÊN CỨU/HỌC TẬP
- ⚠️ Tuân thủ TikTok Terms of Service
- ⚠️ Đừng spam/abuse

## SETUP (15 PHÚT):

### Bước 1: Cài đặt Playwright
```bash
pip install playwright
playwright install chromium
```

### Bước 2: Code mẫu
```python
from playwright.sync_api import sync_playwright
import json
import time

def scrape_tiktok_comments(username, video_limit=5):
    with sync_playwright() as p:
        # Launch browser (có UI để debug)
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Vào profile
        page.goto(f"https://www.tiktok.com/@{username}")
        time.sleep(3)
        
        # Lấy videos
        videos = page.locator('div[data-e2e="user-post-item"]').all()[:video_limit]
        
        all_comments = []
        
        for idx, video in enumerate(videos, 1):
            print(f"Processing video {idx}/{len(videos)}")
            
            # Click vào video
            video.click()
            time.sleep(2)
            
            # Scroll comments
            for _ in range(5):  # Scroll 5 lần
                page.mouse.wheel(0, 1000)
                time.sleep(1)
            
            # Lấy comments
            comments = page.locator('p[data-e2e="comment-text"]').all()
            
            for comment in comments:
                text = comment.inner_text()
                all_comments.append({
                    "video_index": idx,
                    "text": text
                })
            
            # Đóng video
            page.keyboard.press("Escape")
            time.sleep(1)
        
        browser.close()
        
        return all_comments

# Chạy
comments = scrape_tiktok_comments("travinhuniversity", video_limit=10)
print(f"Collected {len(comments)} comments")

# Save
with open("tiktok_comments_scraped.json", "w", encoding="utf-8") as f:
    json.dump(comments, f, indent=2, ensure_ascii=False)
```

### Bước 3: Chạy script
```bash
python scrape_tiktok_playwright.py
```

## LƯU Ý:
- ⏱️ Mất 5-10 phút cho 10 videos
- 🤖 TikTok có thể phát hiện bot → Dùng headless=False
- 🔐 Có thể cần login để xem comments
- ⚠️ Không stable - TikTok thay đổi UI thường xuyên

## RỦI RO:
- ❌ Vi phạm TikTok ToS
- ❌ IP có thể bị block
- ❌ Không ổn định (UI changes)
- ❌ Rate limiting

→ CHỈ DÙNG CHO HỌC TẬP/NGHIÊN CỨU!
"""

print(__doc__)
