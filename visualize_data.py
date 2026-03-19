"""Trực quan hóa dữ liệu TikTok @travinhuniversity

Module này tạo 8 biểu đồ từ dữ liệu đã ghép (merged JSON):

4 biểu đồ chính:
  1. Pie chart - Phân phối sentiment (tích cực/trung tính/tiêu cực)
  2. Bar chart - So sánh tương tác Top 10 video
  3. Line chart - Xu hướng lượt xem theo thời gian
  4. Word cloud - Từ khóa nổi bật trong bình luận

4 biểu đồ bổ sung:
  5. Scatter - Tương quan lượt xem vs Engagement Rate
  6. Stacked bar - Sentiment theo từng video
  7. Donut - Cơ cấu tương tác (likes/shares/saves/comments)
  8. Histogram - Phân bổ độ tin cậy (confidence)

Tất cả biểu đồ lưu tại: reports/charts/
"""
import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
from wordcloud import WordCloud

# Cấu hình font và chất lượng hình ảnh
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 180
plt.rcParams['savefig.dpi'] = 180
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['axes.spines.top'] = False    # Ẩn viền trên
plt.rcParams['axes.spines.right'] = False  # Ẩn viền phải

# Danh sách từ dừng tiếng Việt (loại khỏi word cloud)
VIETNAMESE_STOPWORDS = {
    'la', 'cua', 'va', 'co', 'cho', 'cac', 'trong', 'nay', 'thi', 'ma',
    'nhu', 'duoc', 'khong', 'nhung', 'cung', 'da', 'se', 'den', 'tu',
    'voi', 'mot', 'de', 'qua', 'ra', 'len', 'roi', 'hon', 'noi', 'con',
    'gi', 'vay', 'the', 'tren', 'dau', 'ai', 'bao', 'tai', 'oi', 'nha',
    'ay', 'lam', 'biet', 'phai', 'hay', 'luon', 'het', 'loi', 'nao',
    'sao', 'vua', 'moi', 'dang', 'bi', 'nam', 'ngay', 'di', 'may',
    'minh', 'ban', 'em', 'anh', 'chi', 'hoi', 'day', 'chang', 'gio',
    'khi', 'neu', 'sau', 'truoc', 'bao', 'vi', 'nhieu', 'it',
    'là', 'của', 'và', 'có', 'cho', 'các', 'trong', 'này', 'thì', 'mà',
    'như', 'được', 'không', 'những', 'cũng', 'đã', 'sẽ', 'đến', 'từ',
    'với', 'một', 'để', 'qua', 'ra', 'lên', 'rồi', 'hơn', 'nơi', 'còn',
    'gì', 'vậy', 'thế', 'trên', 'đâu', 'ai', 'bao', 'tại', 'ơi', 'nhà',
    'ấy', 'làm', 'biết', 'phải', 'hay', 'luôn', 'hết', 'lời', 'nào',
    'sao', 'vừa', 'mới', 'đang', 'bị', 'năm', 'ngày', 'đi', 'mấy',
    'mình', 'bạn', 'em', 'anh', 'chị', 'hỏi', 'đây', 'chẳng', 'giờ',
    'khi', 'nếu', 'sau', 'trước', 'bao', 'vì', 'nhiều', 'ít',
    'tôi', 'họ', 'nó', 'hả', 'nhé', 'nhỉ', 'ạ', 'à', 'ừ', 'uh',
    'ok', 'nha', 'hen', 'ha', 'hihi', 'haha', 'huhu',
    'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
}

# Bảng màu chính của dự án
COLORS = {
    'primary': '#1B3A5C',
    'secondary': '#2E86C1',
    'accent': '#E74C3C',
    'success': '#27AE60',
    'warning': '#F39C12',
    'neutral_blue': '#5DADE2',
    'purple': '#8E44AD',
    'dark': '#2C3E50',
}

# Màu cho 3 loại sentiment: xanh lá (positive), xanh dương (neutral), đỏ (negative)
SENTIMENT_COLORS = ['#27AE60', '#5DADE2', '#E74C3C']
# Thư mục lưu biểu đồ
OUTPUT_DIR = Path('reports/charts')


def load_data():
    """Đọc dữ liệu đã ghép từ file merged JSON"""
    data_path = Path('data/merged/tiktok_travinhuniversity_merged.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('videos', []), data.get('comments', [])


def gs(v, key, default=0):
    """Lấy giá trị thống kê từ dict stats lồng nhau"""
    if 'stats' in v and isinstance(v['stats'], dict):
        return v['stats'].get(key, default)
    return v.get(key, default)


def vid(v):
    """Lấy video ID từ entry video"""
    return v.get('id', v.get('video_id', ''))


# =============================================================================
# 1. PIE CHART - BIỂU ĐỒ TRÒN PHÂN PHỐI SENTIMENT
# =============================================================================
def chart_sentiment_pie(comments):
    """
    Vẽ biểu đồ tròn thể hiện tỷ lệ bình luận theo cảm xúc:
    - Xanh lá: Tích cực (Positive)
    - Xanh dương: Trung tính (Neutral)
    - Đỏ: Tiêu cực (Negative)
    """
    counts = {'positive': 0, 'neutral': 0, 'negative': 0}
    for c in comments:
        s = c.get('sentiment', 'neutral').lower()
        if s in counts:
            counts[s] += 1

    labels = ['Tich cuc\n(Positive)', 'Trung tinh\n(Neutral)', 'Tieu cuc\n(Negative)']
    sizes = [counts['positive'], counts['neutral'], counts['negative']]
    total = sum(sizes)
    explode = (0.04, 0.02, 0.04)

    fig, ax = plt.subplots(figsize=(9, 9))
    wedges, texts, autotexts = ax.pie(
        sizes, explode=explode, labels=labels, colors=SENTIMENT_COLORS,
        autopct=lambda p: f'{p:.1f}%\n({int(p/100*total):,})',
        startangle=90, textprops={'fontsize': 14},
        pctdistance=0.72,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2.5}
    )
    for t in autotexts:
        t.set_fontweight('bold')
        t.set_fontsize(13)
    for t in texts:
        t.set_fontsize(13)

    ax.set_title(f'PHAN PHOI SAC THAI BINH LUAN\n(Tong: {total:,} binh luan)',
                 fontsize=18, fontweight='bold', color=COLORS['primary'], pad=25)

    fig.savefig(OUTPUT_DIR / 'sentiment_pie.png')
    plt.close(fig)
    print('  [OK] sentiment_pie.png')


# =============================================================================
# 2. BAR CHART - BIỂU ĐỒ CỘT SO SÁNH TƯƠNG TÁC TOP 10 VIDEO
# =============================================================================
def chart_video_comparison(videos):
    """
    Vẽ biểu đồ cột nhóm so sánh 4 loại tương tác
    (Likes, Shares, Comments, Saves) của Top 10 video nhiều views nhất
    """
    sorted_v = sorted(videos, key=lambda x: gs(x, 'play_count', 0), reverse=True)[:10]

    labels = [f"...{vid(v)[-4:]}" for v in sorted_v]
    likes = [gs(v, 'like_count', 0) for v in sorted_v]
    comments_count = [gs(v, 'comment_count', 0) for v in sorted_v]
    shares = [gs(v, 'share_count', 0) for v in sorted_v]
    saves = [gs(v, 'collect_count', 0) for v in sorted_v]

    x = np.arange(len(labels))
    width = 0.2

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.bar(x - 1.5*width, likes, width, label='Likes', color=COLORS['accent'], alpha=0.85)
    ax.bar(x - 0.5*width, shares, width, label='Shares', color=COLORS['secondary'], alpha=0.85)
    ax.bar(x + 0.5*width, comments_count, width, label='Comments', color=COLORS['warning'], alpha=0.85)
    ax.bar(x + 1.5*width, saves, width, label='Saves', color=COLORS['success'], alpha=0.85)

    for i, v in enumerate(sorted_v):
        plays = gs(v, 'play_count', 0)
        play_str = f'{plays/1e6:.1f}M' if plays >= 1e6 else f'{plays/1e3:.0f}K'
        max_val = max(likes[i], shares[i], comments_count[i], saves[i])
        ax.text(i, max_val * 1.05, f'Views: {play_str}', ha='center', va='bottom',
                fontsize=9, fontweight='bold', color=COLORS['primary'])

    ax.set_xlabel('Video ID (4 so cuoi)', fontsize=13, fontweight='bold')
    ax.set_ylabel('So luong tuong tac', fontsize=13, fontweight='bold')
    ax.set_title('SO SANH TUONG TAC - TOP 10 VIDEOS NHIEU VIEWS NHAT',
                 fontsize=18, fontweight='bold', color=COLORS['primary'], pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.legend(fontsize=12, loc='upper right')
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(
        lambda y, _: f'{y/1e3:.0f}K' if y >= 1000 else f'{y:.0f}'))

    fig.savefig(OUTPUT_DIR / 'video_comparison_bar.png')
    plt.close(fig)
    print('  [OK] video_comparison_bar.png')


# =============================================================================
# 3. LINE CHART - BIỂU ĐỒ ĐƯỜNG XU HƯỚNG LƯỢT XEM
# =============================================================================
def chart_views_trend(videos):
    """
    Vẽ 2 biểu đồ đường:
    - Trên: Lượt xem từng video theo thời gian đăng + đường trung bình trượt
    - Dưới: Tổng lượt xem tích lũy theo thời gian
    """
    dated = []
    for v in videos:
        ct = v.get('create_time', '')
        if not ct:
            continue
        try:
            dt = datetime.fromisoformat(ct.replace('Z', '+00:00'))
            dated.append((dt, gs(v, 'play_count', 0), gs(v, 'like_count', 0)))
        except (ValueError, TypeError):
            continue

    dated.sort(key=lambda x: x[0])
    dates = [d[0] for d in dated]
    plays = [d[1] for d in dated]
    cum_plays = np.cumsum(plays)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={'height_ratios': [3, 2]})

    # Top: Individual video plays
    scatter = ax1.scatter(dates, plays, s=[max(30, p/15000) for p in plays],
                          c=plays, cmap='YlOrRd', alpha=0.7, edgecolors='white', linewidth=0.8)
    ax1.plot(dates, plays, color=COLORS['secondary'], alpha=0.3, linewidth=1, linestyle='--')

    if len(plays) >= 5:
        window = 5
        ma = np.convolve(plays, np.ones(window)/window, mode='valid')
        ma_dates = dates[window-1:]
        ax1.plot(ma_dates, ma, color=COLORS['accent'], linewidth=2.5,
                 label=f'Trung binh truot ({window} videos)', zorder=5)

    ax1.set_ylabel('Luot xem / video', fontsize=12, fontweight='bold')
    ax1.set_title('XU HUONG LUOT XEM THEO THOI GIAN DANG',
                  fontsize=18, fontweight='bold', color=COLORS['primary'], pad=15)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(
        lambda y, _: f'{y/1e6:.1f}M' if y >= 1e6 else (f'{y/1e3:.0f}K' if y >= 1000 else f'{y:.0f}')))
    ax1.legend(fontsize=11)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))

    # Bottom: Cumulative
    ax2.fill_between(dates, cum_plays, alpha=0.3, color=COLORS['secondary'])
    ax2.plot(dates, cum_plays, color=COLORS['primary'], linewidth=2.5)
    ax2.set_xlabel('Thoi gian dang video', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Tong views tich luy', fontsize=12, fontweight='bold')
    ax2.set_title('TONG LUOT XEM TICH LUY', fontsize=14, fontweight='bold', color=COLORS['dark'])
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(
        lambda y, _: f'{y/1e6:.1f}M' if y >= 1e6 else f'{y/1e3:.0f}K'))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / 'views_trend_line.png')
    plt.close(fig)
    print('  [OK] views_trend_line.png')


# =============================================================================
# 4. WORD CLOUD - ĐÁM MÂY TỪ KHÓA BÌNH LUẬN
# =============================================================================
def chart_wordcloud(comments):
    """
    Tạo đám mây từ khóa từ tất cả bình luận.
    Từ xuất hiện nhiều hơn sẽ có cỡ chữ lớn hơn.
    Loại bỏ từ dừng tiếng Việt (stopwords).
    Cũng tạo riêng word cloud cho bình luận tích cực và tiêu cực.
    """
    all_text = ' '.join(c.get('text', '') for c in comments)
    all_text = re.sub(r'[^\w\s]', ' ', all_text)
    all_text = re.sub(r'\d+', '', all_text)
    all_text = re.sub(r'\s+', ' ', all_text).strip()

    wc = WordCloud(
        width=1600, height=900,
        background_color='white',
        max_words=150,
        stopwords=VIETNAMESE_STOPWORDS,
        colormap='Set2',
        max_font_size=120,
        min_font_size=10,
        collocations=True,
        prefer_horizontal=0.7,
        margin=10,
    )
    wc.generate(all_text)

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.imshow(wc, interpolation='bilinear')
    ax.set_title('TU KHOA NOI BAT TRONG BINH LUAN\n(@travinhuniversity - 1,222 binh luan)',
                 fontsize=18, fontweight='bold', color=COLORS['primary'], pad=15)
    ax.axis('off')
    fig.savefig(OUTPUT_DIR / 'wordcloud.png')
    plt.close(fig)
    print('  [OK] wordcloud.png')

    # Sentiment-specific word clouds
    for sentiment, color_map, label in [
        ('positive', 'Greens', 'TICH CUC'),
        ('negative', 'Reds', 'TIEU CUC'),
    ]:
        texts = ' '.join(c.get('text', '') for c in comments
                         if c.get('sentiment', '').lower() == sentiment)
        texts = re.sub(r'[^\w\s]', ' ', texts)
        texts = re.sub(r'\d+', '', texts)
        if len(texts.split()) < 10:
            continue

        wc_s = WordCloud(
            width=800, height=500, background_color='white',
            max_words=80, stopwords=VIETNAMESE_STOPWORDS,
            colormap=color_map, max_font_size=80,
        )
        wc_s.generate(texts)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(wc_s, interpolation='bilinear')
        ax.set_title(f'TU KHOA - BINH LUAN {label}',
                     fontsize=16, fontweight='bold', color=COLORS['primary'], pad=10)
        ax.axis('off')
        fig.savefig(OUTPUT_DIR / f'wordcloud_{sentiment}.png')
        plt.close(fig)
        print(f'  [OK] wordcloud_{sentiment}.png')


# =============================================================================
# 5. SCATTER - BIỂU ĐỒ PHÂN TÁN: LƯỢT XEM vs ENGAGEMENT
# =============================================================================
def chart_plays_vs_engagement(videos):
    """
    Vẽ biểu đồ phân tán thể hiện mối quan hệ giữa
    lượt xem (trục X) và tỷ lệ tương tác (trục Y).
    Kích thước chấm tỷ lệ với lượt xem.
    Đường ngang là engagement rate trung bình.
    """
    data_points = []
    for v in videos:
        p = gs(v, 'play_count', 0)
        if p < 500:
            continue
        likes = gs(v, 'like_count', 0)
        cmts = gs(v, 'comment_count', 0)
        shares = gs(v, 'share_count', 0)
        eng = (likes + cmts + shares) / p * 100
        data_points.append((p, eng))

    plays = [d[0] for d in data_points]
    eng_rates = [d[1] for d in data_points]
    avg_eng = np.mean(eng_rates)

    fig, ax = plt.subplots(figsize=(12, 7))
    sizes = [max(30, min(400, p / 4000)) for p in plays]
    scatter = ax.scatter(plays, eng_rates, s=sizes, alpha=0.6,
                         c=eng_rates, cmap='RdYlGn', edgecolors='white', linewidth=0.8)
    plt.colorbar(scatter, ax=ax, label='Engagement Rate (%)', shrink=0.8)

    ax.axhline(y=avg_eng, color=COLORS['accent'], linestyle='--', alpha=0.7, linewidth=2)
    ax.text(max(plays)*0.6, avg_eng + 0.4, f'Trung binh: {avg_eng:.2f}%',
            color=COLORS['accent'], fontsize=12, fontweight='bold')

    ax.set_xlabel('Luot xem (Plays)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Engagement Rate (%)', fontsize=13, fontweight='bold')
    ax.set_title('TUONG QUAN LUOT XEM vs ENGAGEMENT RATE',
                 fontsize=18, fontweight='bold', color=COLORS['primary'], pad=15)
    ax.set_xscale('log')
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(
        lambda x, _: f'{x/1e6:.1f}M' if x >= 1e6 else (f'{x/1e3:.0f}K' if x >= 1e3 else f'{x:.0f}')))

    fig.savefig(OUTPUT_DIR / 'plays_vs_engagement.png')
    plt.close(fig)
    print('  [OK] plays_vs_engagement.png')


# =============================================================================
# 6. STACKED BAR - BIỂU ĐỒ CỘT CHỒNG SENTIMENT THEO VIDEO
# =============================================================================
def chart_video_sentiment(videos, comments):
    """
    Vẽ biểu đồ cột chồng thể hiện số lượng bình luận
    positive/neutral/negative cho Top 15 video có nhiều bình luận nhất.
    """
    vc = {}
    for c in comments:
        v_id = str(c.get('video_id', ''))
        s = c.get('sentiment', 'neutral').lower()
        if v_id not in vc:
            vc[v_id] = {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}
        if s in vc[v_id]:
            vc[v_id][s] += 1
        vc[v_id]['total'] += 1

    top = sorted(vc.items(), key=lambda x: x[1]['total'], reverse=True)[:15]
    labels = [f"...{v[-4:]}" for v, _ in top]
    pos = [d['positive'] for _, d in top]
    neu = [d['neutral'] for _, d in top]
    neg = [d['negative'] for _, d in top]
    x = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.bar(x, pos, label='Positive', color=SENTIMENT_COLORS[0], alpha=0.85)
    ax.bar(x, neu, bottom=pos, label='Neutral', color=SENTIMENT_COLORS[1], alpha=0.85)
    ax.bar(x, neg, bottom=[p+n for p, n in zip(pos, neu)], label='Negative',
           color=SENTIMENT_COLORS[2], alpha=0.85)

    for i in range(len(labels)):
        total = pos[i] + neu[i] + neg[i]
        ax.text(i, total + 0.5, str(total), ha='center', fontsize=10, fontweight='bold')

    ax.set_xlabel('Video ID', fontsize=12, fontweight='bold')
    ax.set_ylabel('So luong binh luan', fontsize=12, fontweight='bold')
    ax.set_title('PHAN BO SENTIMENT THEO VIDEO (TOP 15)',
                 fontsize=16, fontweight='bold', color=COLORS['primary'], pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10, rotation=45, ha='right')
    ax.legend(fontsize=12)

    fig.savefig(OUTPUT_DIR / 'video_sentiment_stack.png')
    plt.close(fig)
    print('  [OK] video_sentiment_stack.png')


# =============================================================================
# 7. DONUT - BIỂU ĐỒ VÀNH KHĂN TỔNG QUAN TƯƠNG TÁC
# =============================================================================
def chart_engagement_donut():
    """
    Vẽ biểu đồ donut (vành khăn) thể hiện cơ cấu tương tác:
    - Likes: 367,185 (79.1%)
    - Shares: 77,377 (16.7%)
    - Saves: 13,353 (2.9%)
    - Comments: 6,035 (1.3%)
    Tổng: 463,950 tương tác
    """
    labels = ['Likes\n367,185', 'Shares\n77,377', 'Saves\n13,353', 'Comments\n6,035']
    sizes = [367185, 77377, 13353, 6035]
    colors = [COLORS['accent'], COLORS['secondary'], COLORS['warning'], COLORS['success']]

    fig, ax = plt.subplots(figsize=(9, 9))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors,
        autopct='%1.1f%%', startangle=90,
        textprops={'fontsize': 13},
        pctdistance=0.82,
        wedgeprops={'width': 0.4, 'edgecolor': 'white', 'linewidth': 2.5}
    )
    for t in autotexts:
        t.set_fontweight('bold')
        t.set_fontsize(12)

    ax.text(0, 0, '463,950\nTong Tuong Tac', ha='center', va='center',
            fontsize=18, fontweight='bold', color=COLORS['primary'])

    ax.set_title('CO CAU TUONG TAC TIKTOK\n(100 videos @travinhuniversity)',
                 fontsize=18, fontweight='bold', color=COLORS['primary'], pad=20)

    fig.savefig(OUTPUT_DIR / 'engagement_donut.png')
    plt.close(fig)
    print('  [OK] engagement_donut.png')


# =============================================================================
# 8. HISTOGRAM - BIỂU ĐỒ PHÂN BỔ ĐỘ TIN CẬY
# =============================================================================
def chart_confidence(comments):
    """
    Vẽ histogram thể hiện phân bổ độ tin cậy (confidence score)
    của kết quả sentiment cho 3 loại: positive, neutral, negative.
    Đường kẻ dọc tại 0.9 (High) và 0.7 (Medium).
    """
    fig, ax = plt.subplots(figsize=(11, 6))

    for s, color, label in [('positive', SENTIMENT_COLORS[0], 'Positive'),
                             ('neutral', SENTIMENT_COLORS[1], 'Neutral'),
                             ('negative', SENTIMENT_COLORS[2], 'Negative')]:
        vals = [c.get('confidence', 0) for c in comments
                if c.get('confidence') and c.get('sentiment', '').lower() == s]
        ax.hist(vals, bins=20, alpha=0.55, color=color, label=label, edgecolor='white')

    ax.axvline(x=0.9, color='gray', linestyle='--', alpha=0.6, linewidth=1.5)
    ax.axvline(x=0.7, color='gray', linestyle=':', alpha=0.6, linewidth=1.5)
    ax.text(0.91, ax.get_ylim()[1]*0.9, 'High', fontsize=10, color='gray')
    ax.text(0.71, ax.get_ylim()[1]*0.9, 'Medium', fontsize=10, color='gray')

    ax.set_xlabel('Confidence Score', fontsize=13, fontweight='bold')
    ax.set_ylabel('So luong', fontsize=13, fontweight='bold')
    ax.set_title('PHAN BO CONFIDENCE SCORE THEO SENTIMENT\n(50.2% High >= 0.9)',
                 fontsize=16, fontweight='bold', color=COLORS['primary'], pad=15)
    ax.legend(fontsize=12)

    fig.savefig(OUTPUT_DIR / 'confidence_hist.png')
    plt.close(fig)
    print('  [OK] confidence_hist.png')


# =============================================================================
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('  TRUC QUAN HOA DU LIEU TIKTOK @travinhuniversity')
    print('=' * 60)

    videos, comments = load_data()
    print(f'  Loaded: {len(videos)} videos, {len(comments)} comments\n')

    print('[1/4] Pie chart - Sentiment...')
    chart_sentiment_pie(comments)

    print('[2/4] Bar chart - So sanh tuong tac...')
    chart_video_comparison(videos)

    print('[3/4] Line chart - Xu huong luot xem...')
    chart_views_trend(videos)

    print('[4/4] Word cloud - Tu khoa binh luan...')
    chart_wordcloud(comments)

    print('\n--- Bieu do bo sung ---')
    print('[5] Scatter - Plays vs Engagement...')
    chart_plays_vs_engagement(videos)

    print('[6] Stacked bar - Sentiment theo video...')
    chart_video_sentiment(videos, comments)

    print('[7] Donut - Tong quan tuong tac...')
    chart_engagement_donut()

    print('[8] Histogram - Confidence...')
    chart_confidence(comments)

    print(f'\n[OK] Hoan tat! {len(list(OUTPUT_DIR.glob("*.png")))} bieu do tai {OUTPUT_DIR}/')
    print('=' * 60)


if __name__ == '__main__':
    main()
