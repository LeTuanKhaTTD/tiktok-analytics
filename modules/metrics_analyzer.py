"""
============================================================================
MODULE PHÂN TÍCH METRICS - TRÁI TIM CỦA HỆ THỐNG
============================================================================

Đây là module XỬ LÝ CHÍNH của toàn bộ hệ thống phân tích YouTube.

CHỨC NĂNG CHÍNH:
1.  Tính toán metrics (engagement rate, virality score, interaction rate)
2.  Phân tích xu hướng theo thời gian (trending analysis)
3.  Tạo visualizations (4 loại biểu đồ khác nhau)
4.  Sinh báo cáo tổng hợp dạng text
5.  Phát hiện insights và đưa ra recommendations

QUY TRÌNH XỬ LÝ:
    Raw Data (từ YouTube Scraper)
         ↓
    calculate_engagement_metrics() → Tính metrics cho từng video
         ↓
    analyze_profile_metrics() → Phân tích toàn bộ channel
         ↓
    create_visualizations() → Tạo 4 biểu đồ
         ↓
    generate_report() → Sinh báo cáo text

INPUT: Dictionary chứa dữ liệu video từ YouTube (views, likes, comments)
OUTPUT: Metrics, biểu đồ PNG/HTML, báo cáo TXT, dữ liệu CSV

Tác giả: YouTube Analytics AI Module
Ngày tạo: 2026-03-02
============================================================================
"""

from typing import Dict, List
import pandas as pd          # Xử lý dữ liệu dạng bảng
import numpy as np           # Tính toán số học
import matplotlib.pyplot as plt  # Vẽ biểu đồ tĩnh
import seaborn as sns        # Biểu đồ đẹp hơn
from datetime import datetime
import plotly.graph_objects as go  # Biểu đồ interactive
import plotly.express as px
from pathlib import Path
import json


class MetricsAnalyzer:
    """
    ============================================================================
    CLASS METRICS ANALYZER - TRUNG TÂM XỬ LÝ DỮ LIỆU
    ============================================================================
    
    Class này chịu trách nhiệm xử lý toàn bộ quá trình phân tích metrics.
    
    CÁC METHOD CHÍNH:
    -----------------
    1. calculate_engagement_metrics(video_data)
       → Tính engagement rate, virality score cho 1 video
       
    2. analyze_profile_metrics(profile_data)
       → Phân tích toàn bộ channel, tìm top videos, xu hướng
       
    3. create_visualizations(metrics_data, sentiment_data)
       → Tạo 4 loại biểu đồ (PNG + HTML interactive)
       
    4. generate_report(profile_data, metrics_data, sentiment_data)
       → Sinh báo cáo text với insights và recommendations
    
    CÔNG THỨC TÍNH METRICS:
    -----------------------
    • Engagement Rate = (likes + comments + shares) / views × 100
    • Interaction Rate = (likes + comments + shares + saves) / views × 100
    • Virality Score = (shares×10 + likes + comments×2) / views
    • Like/Comment/Share Rate = (số lượng tương ứng) / views × 100
    
    ============================================================================
    """
    
    def __init__(self):
        """
        Khởi tạo Metrics Analyzer
        
        SETUP:
        - Style cho matplotlib: seaborn-v0_8-darkgrid (đẹp, dễ đọc)
        - Color palette: husl (màu sắc hài hòa)
        """
        # Set style cho matplotlib để biểu đồ đẹp hơn
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
        
    def calculate_engagement_metrics(self, video_data: Dict) -> Dict:
        """
        ========================================================================
        HÀM TÍNH TOÁN METRICS CHO 1 VIDEO - CORE FUNCTION
        ========================================================================
        
        Đây là hàm QUAN TRỌNG NHẤT, tính toán tất cả các chỉ số đo lường
        hiệu quả của một video dựa trên công thức chuẩn ngành social media.
        
        INPUT:
        ------
        video_data: Dictionary chứa thông tin video với cấu trúc:
            {
                'video_id': str,
                'stats': {
                    'play_count': int,  # Số lượt xem
                    'like_count': int,  # Số lượt thích
                    'comment_count': int,  # Số comments
                    'share_count': int,  # Số lượt chia sẻ (nếu có)
                    'save_count': int   # Số lượt lưu (favorite)
                }
            }
        
        OUTPUT:
        -------
        Dictionary chứa các metrics đã tính:
            {
                'video_id': str,
                'engagement_rate': float,    # Tỷ lệ tương tác chính
                'interaction_rate': float,   # Tỷ lệ tương tác tổng
                'like_rate': float,          # Tỷ lệ like/views
                'comment_rate': float,       # Tỷ lệ comment/views
                'share_rate': float,         # Tỷ lệ share/views
                'save_rate': float,          # Tỷ lệ save/views
                'virality_score': float,     # Điểm khả năng lan truyền
                'total_interactions': int,   # Tổng số tương tác
                'stats': dict                # Stats gốc
            }
        
        CÔNG THỨC TÍNH:
        ---------------
        1. Engagement Rate = (likes + comments + shares) / views × 100
           → Đo lường mức độ tương tác cơ bản
           → Cao > 5% là tốt, > 10% là xuất sắc
        
        2. Interaction Rate = (likes + comments + shares + saves) / views × 100
           → Đo lường tổng thể mọi hành động
           → Bao gồm cả saves/favorites
        
        3. Virality Score = (shares×10 + likes + comments×2) / views
           → Đo lường khả năng lan truyền
           → Shares có trọng số cao nhất (×10)
           → Comments có trọng số vừa (×2)
           → Likes có trọng số thấp nhất (×1)
        
        4. Like/Comment/Share/Save Rate = (số lượng) / views × 100
           → Đo lường từng loại tương tác riêng biệt
        
        LƯU Ý:
        ------
        - Tất cả tỷ lệ % được làm tròn 2 chữ số thập phân
        - Virality score làm tròn 4 chữ số thập phân (độ chính xác cao hơn)
        - Nếu views = 0, tất cả rate = 0 (tránh chia cho 0)
        ========================================================================
        """
        # Lấy stats từ video data
        stats = video_data.get('stats', {})
        
        # Lấy từng metric riêng biệt (hỗ trợ YouTube Data API format)
        # YouTube: like_count, comment_count, view_count
        likes = stats.get('likes', stats.get('like_count', 0))
        comments = stats.get('comments', stats.get('comment_count', 0))
        shares = stats.get('shares', stats.get('share_count', 0))
        plays = stats.get('plays', stats.get('play_count', stats.get('view_count', 0)))
        saves = stats.get('saves', stats.get('save_count', stats.get('favorite_count', 0)))
        
        # CÔNG THỨC 1: Engagement Rate (Tỷ lệ tương tác chính)
        # = (likes + comments + shares) / plays × 100
        # Đây là chỉ số QUAN TRỌNG NHẤT để đánh giá hiệu quả video
        engagement_rate = ((likes + comments + shares) / plays * 100) if plays > 0 else 0
        
        # CÔNG THỨC 2: Interaction Rate (Tỷ lệ tương tác tổng)
        # = (likes + comments + shares + saves) / plays × 100
        # Bao gồm cả saves/favorites để đánh giá toàn diện hơn
        interaction_rate = ((likes + comments + shares + saves) / plays * 100) if plays > 0 else 0
        
        # CÔNG THỨC 3: Like Rate (Tỷ lệ thích)
        # = likes / plays × 100
        # Đo lường mức độ người xem thích video
        like_rate = (likes / plays * 100) if plays > 0 else 0
        
        # CÔNG THỨC 4: Comment Rate (Tỷ lệ bình luận)
        # = comments / plays × 100
        # Comment thường có giá trị cao hơn like (cần effort hơn)
        comment_rate = (comments / plays * 100) if plays > 0 else 0
        
        # CÔNG THỨC 5: Share Rate (Tỷ lệ chia sẻ)
        # = shares / plays × 100
        # Share là chỉ số CỰC KỲ QUAN TRỌNG (người dùng recommend cho bạn bè)
        share_rate = (shares / plays * 100) if plays > 0 else 0
        
        # CÔNG THỨC 6: Save Rate (Tỷ lệ lưu)
        # = saves / plays × 100
        # Save cho thấy video có giá trị lâu dài (muốn xem lại)
        save_rate = (saves / plays * 100) if plays > 0 else 0
        
        # CÔNG THỨC 7: Virality Score (Điểm lan truyền)
        # = (shares×10 + likes + comments×2) / plays
        # TRỌNG SỐ: shares (×10) > comments (×2) > likes (×1)
        # Lý do: Share có impact cao nhất (reach mới), comments cần effort,
        # likes dễ nhất nên trọng số thấp nhất
        virality_score = (shares * 10 + likes + comments * 2) / plays if plays > 0 else 0
        
        return {
            'video_id': video_data.get('video_id'),
            'engagement_rate': round(engagement_rate, 2),
            'interaction_rate': round(interaction_rate, 2),
            'like_rate': round(like_rate, 2),
            'comment_rate': round(comment_rate, 2),
            'share_rate': round(share_rate, 2),
            'save_rate': round(save_rate, 2),
            'virality_score': round(virality_score, 4),
            'total_interactions': likes + comments + shares + saves,
            'stats': stats
        }
    
    def analyze_profile_metrics(self, profile_data: Dict) -> Dict:
        """
        ========================================================================
        HÀM PHÂN TÍCH TOÀN BỘ CHANNEL - MAIN ANALYSIS FUNCTION
        ========================================================================
        
        Đây là hàm XỬ LÝ CHÍNH, phân tích metrics cho cả channel/profile.
        
        QUY TRÌNH HOẠT ĐỘNG:
        --------------------
        1. Lặp qua từng video → tính metrics riêng lẻ
        2. Tổng hợp metrics thành DataFrame (dễ xử lý)
        3. Tính toán thống kê tổng hợp (average, median, std)
        4. Tìm top performing videos (best engagement, most viral, most liked)
        5. Phân tích xu hướng theo thời gian (3 periods: early/mid/recent)
        
        INPUT:
        ------
        profile_data: Dictionary chứa dữ liệu channel:
            {
                'username': str,           # Tên channel
                'user_id': str,            # Channel ID
                'follower_count': int,     # Số subscribers
                'videos': [                # List các videos
                    {
                        'id': str,
                        'stats': {...},
                        'create_time': str,
                        'description': str,
                        'comments': [...]
                    },
                    ...
                ]
            }
        
        OUTPUT:
        -------
        Dictionary chứa kết quả phân tích:
            {
                'summary': {               # Thống kê tổng hợp
                    'username': str,
                    'total_videos': int,
                    'total_plays': int,    # Tổng views
                    'total_likes': int,
                    'total_comments': int,
                    'total_shares': int,
                    'avg_engagement_rate': float,  # TB engagement
                    'median_engagement_rate': float,
                    'std_engagement_rate': float,
                    ...
                },
                'video_metrics': [         # Metrics từng video
                    {...},
                    ...
                ],
                'top_videos': {            # Top 3 videos xuất sắc
                    'best_engagement': {...},   # Video engagement cao nhất
                    'most_viral': {...},        # Video lan truyền mạnh nhất
                    'most_liked': {...}         # Video nhiều like nhất
                },
                'trends': {                # Xu hướng theo thời gian
                    'early_avg_engagement': float,    # Giai đoạn đầu
                    'mid_avg_engagement': float,      # Giai đoạn giữa
                    'recent_avg_engagement': float,   # Giai đoạn gần đây
                    'trend': str  # 'improving' hoặc 'declining'
                },
                'dataframe': DataFrame     # Pandas DataFrame để xử lý thêm
            }
        
        PHÂN TÍCH XU HƯỚNG:
        -------------------
        - Chia videos thành 3 giai đoạn theo thời gian đăng
        - So sánh engagement rate giữa các giai đoạn
        - Xác định trend: improving (tăng) hay declining (giảm)
        - Giúp nhận biết chiến lược content có hiệu quả không
        
        ========================================================================
        """
        # Lấy danh sách videos từ profile data
        videos = profile_data.get('videos', [])
        
        # In header để user biết đang xử lý
        print(f"\n{'='*60}")
        print(f" PHÂN TÍCH METRICS VÀ TƯƠNG TÁC")
        print(f"{'='*60}\n")
        
        # BƯỚC 1: Tính metrics cho TỪNG video riêng lẻ
        # Dùng hàm calculate_engagement_metrics() đã define ở trên
        video_metrics = []
        for video in videos:
            metrics = self.calculate_engagement_metrics(video)
            metrics['create_time'] = video.get('create_time')
            metrics['description'] = video.get('description', '')[:50]
            video_metrics.append(metrics)
        
        # Convert sang DataFrame để phân tích
        df = pd.DataFrame(video_metrics)
        
        # Tính toán thống kê tổng hợp
        summary = {
            'username': profile_data.get('username'),
            'total_videos': len(videos),
            'total_plays': df['stats'].apply(lambda x: x.get('plays', 0)).sum(),
            'total_likes': df['stats'].apply(lambda x: x.get('likes', 0)).sum(),
            'total_comments': df['stats'].apply(lambda x: x.get('comments', 0)).sum(),
            'total_shares': df['stats'].apply(lambda x: x.get('shares', 0)).sum(),
            'total_saves': df['stats'].apply(lambda x: x.get('saves', 0)).sum(),
            'avg_engagement_rate': round(df['engagement_rate'].mean(), 2),
            'avg_interaction_rate': round(df['interaction_rate'].mean(), 2),
            'avg_like_rate': round(df['like_rate'].mean(), 2),
            'avg_comment_rate': round(df['comment_rate'].mean(), 2),
            'avg_share_rate': round(df['share_rate'].mean(), 2),
            'avg_save_rate': round(df['save_rate'].mean(), 2),
            'avg_virality_score': round(df['virality_score'].mean(), 4),
            'median_engagement_rate': round(df['engagement_rate'].median(), 2),
            'std_engagement_rate': round(df['engagement_rate'].std(), 2),
        }
        
        # Tìm video có performance tốt nhất
        best_engagement_idx = df['engagement_rate'].idxmax()
        best_virality_idx = df['virality_score'].idxmax()
        most_liked_idx = df['stats'].apply(lambda x: x.get('likes', 0)).idxmax()
        
        top_videos = {
            'best_engagement': video_metrics[best_engagement_idx],
            'most_viral': video_metrics[best_virality_idx],
            'most_liked': video_metrics[most_liked_idx]
        }
        
        # Phân tích xu hướng
        df_sorted = df.sort_values('create_time')
        
        # Chia thành 3 giai đoạn
        n = len(df_sorted)
        period_size = n // 3
        
        if n >= 3:
            early_period = df_sorted.iloc[:period_size]
            mid_period = df_sorted.iloc[period_size:period_size*2]
            recent_period = df_sorted.iloc[period_size*2:]
            
            trends = {
                'early_avg_engagement': round(early_period['engagement_rate'].mean(), 2),
                'mid_avg_engagement': round(mid_period['engagement_rate'].mean(), 2),
                'recent_avg_engagement': round(recent_period['engagement_rate'].mean(), 2),
                'trend': 'improving' if recent_period['engagement_rate'].mean() > early_period['engagement_rate'].mean() else 'declining'
            }
        else:
            trends = None
        
        print(f"✓ Phân tích metrics hoàn tất!")
        print(f"\n KẾT QUẢ TỔNG QUAN:")
        print(f"  Tổng lượt xem: {summary['total_plays']:,}")
        print(f"  Tổng likes: {summary['total_likes']:,}")
        print(f"  Tổng comments: {summary['total_comments']:,}")
        print(f"  Tổng shares: {summary['total_shares']:,}")
        print(f"  Engagement rate trung bình: {summary['avg_engagement_rate']:.2f}%")
        print(f"  Virality score trung bình: {summary['avg_virality_score']:.4f}")
        
        return {
            'summary': summary,
            'video_metrics': video_metrics,
            'top_videos': top_videos,
            'trends': trends,
            'dataframe': df
        }
    
    def create_visualizations(self, metrics_data: Dict, sentiment_data: Dict, 
                            output_dir: str = 'reports') -> Dict:
        """
        Tạo các biểu đồ trực quan
        
        Args:
            metrics_data: Dữ liệu metrics từ analyze_profile_metrics
            sentiment_data: Dữ liệu sentiment từ SentimentAnalyzer
            output_dir: Thư mục lưu biểu đồ
            
        Returns:
            Dictionary chứa đường dẫn các file đã tạo
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"\n Đang tạo biểu đồ trực quan...")
        
        df = metrics_data['dataframe']
        summary = metrics_data['summary']
        
        created_files = []
        
        # 1. Engagement Metrics Overview
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f"YouTube Analytics - {summary['username']}", fontsize=16, fontweight='bold')
        
        # Engagement rates
        rates = ['like_rate', 'comment_rate', 'share_rate', 'save_rate']
        rate_values = [summary['avg_like_rate'], summary['avg_comment_rate'], 
                      summary['avg_share_rate'], summary['avg_save_rate']]
        
        axes[0, 0].bar(rates, rate_values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'])
        axes[0, 0].set_title('Average Interaction Rates (%)')
        axes[0, 0].set_ylabel('Rate (%)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Total interactions
        totals = ['Plays', 'Likes', 'Comments', 'Shares', 'Saves']
        total_values = [summary['total_plays'], summary['total_likes'], 
                       summary['total_comments'], summary['total_shares'], summary['total_saves']]
        
        axes[0, 1].bar(totals, total_values, color=['#95E1D3', '#F38181', '#AA96DA', '#FCBAD3', '#FFFFD2'])
        axes[0, 1].set_title('Total Interactions')
        axes[0, 1].set_ylabel('Count')
        axes[0, 1].tick_params(axis='x', rotation=45)
        axes[0, 1].ticklabel_format(style='plain', axis='y')
        
        # Engagement rate distribution
        axes[1, 0].hist(df['engagement_rate'], bins=20, color='#667EEA', alpha=0.7, edgecolor='black')
        axes[1, 0].axvline(summary['avg_engagement_rate'], color='red', linestyle='--', linewidth=2, label='Average')
        axes[1, 0].set_title('Engagement Rate Distribution')
        axes[1, 0].set_xlabel('Engagement Rate (%)')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].legend()
        
        # Virality score distribution
        axes[1, 1].hist(df['virality_score'], bins=20, color='#F093FB', alpha=0.7, edgecolor='black')
        axes[1, 1].axvline(summary['avg_virality_score'], color='red', linestyle='--', linewidth=2, label='Average')
        axes[1, 1].set_title('Virality Score Distribution')
        axes[1, 1].set_xlabel('Virality Score')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].legend()
        
        plt.tight_layout()
        file1 = output_path / 'engagement_overview.png'
        plt.savefig(file1, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(str(file1))
        print(f"  ✓ Đã tạo: {file1.name}")
        
        # 2. Sentiment Analysis Visualization
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(f"Sentiment Analysis - @{summary['username']}", fontsize=16, fontweight='bold')
        
        # Video sentiment distribution
        video_sent = sentiment_data['video_sentiment_distribution']
        colors_sent = ['#2ECC71', '#E74C3C', '#95A5A6']
        
        # Video sentiment distribution
        video_sent_total = video_sent['positive'] + video_sent['negative'] + video_sent['neutral']
        if video_sent_total > 0:
            axes[0].pie([video_sent['positive'], video_sent['negative'], video_sent['neutral']], 
                       labels=['Positive', 'Negative', 'Neutral'],
                       colors=colors_sent,
                       autopct='%1.1f%%',
                       startangle=90)
        else:
            axes[0].pie([1], labels=['No Data'], colors=['#CCCCCC'])
            axes[0].text(0, 0, 'No video\nsentiment data', ha='center', va='center', fontsize=12)
        axes[0].set_title('Video Sentiment Distribution')
        
        # Comments sentiment distribution
        comment_sent = sentiment_data['comments_sentiment_distribution']
        comment_sent_total = comment_sent['positive'] + comment_sent['negative'] + comment_sent['neutral']
        
        if comment_sent_total > 0:
            axes[1].pie([comment_sent['positive'], comment_sent['negative'], comment_sent['neutral']], 
                       labels=['Positive', 'Negative', 'Neutral'],
                       colors=colors_sent,
                       autopct='%1.1f%%',
                       startangle=90)
        else:
            axes[1].pie([1], labels=['No Data'], colors=['#CCCCCC'])
            axes[1].text(0, 0, 'No comments\nfound', ha='center', va='center', fontsize=12)
        axes[1].set_title('Comments Sentiment Distribution')
        
        plt.tight_layout()
        file2 = output_path / 'sentiment_analysis.png'
        plt.savefig(file2, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(str(file2))
        print(f"   Đã tạo: {file2.name}")
        
        # 3. Performance over time (Interactive Plotly)
        df_sorted = df.sort_values('create_time')
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=list(range(len(df_sorted))),
            y=df_sorted['engagement_rate'],
            mode='lines+markers',
            name='Engagement Rate',
            line=dict(color='#667EEA', width=2),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=list(range(len(df_sorted))),
            y=df_sorted['virality_score'] * 10,  # Scale for visibility
            mode='lines+markers',
            name='Virality Score (x10)',
            line=dict(color='#F093FB', width=2),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title=f'Performance Over Time - @{summary["username"]}',
            xaxis_title='Video Index (Chronological)',
            yaxis_title='Rate (%)',
            hovermode='x unified',
            template='plotly_white'
        )
        
        file3 = output_path / 'performance_timeline.html'
        fig.write_html(file3)
        created_files.append(str(file3))
        print(f"   Đã tạo: {file3.name}")
        
        # 4. Top Videos Comparison
        top_videos_data = []
        for key, video in metrics_data['top_videos'].items():
            top_videos_data.append({
                'Type': key.replace('_', ' ').title(),
                'Engagement Rate': video['engagement_rate'],
                'Likes': video['stats'].get('likes', video['stats'].get('like_count', 0)),
                'Comments': video['stats'].get('comments', video['stats'].get('comment_count', 0)),
                'Shares': video['stats'].get('shares', video['stats'].get('share_count', 0))
            })
        
        df_top = pd.DataFrame(top_videos_data)
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(f"Top Performing Videos - @{summary['username']}", fontsize=16, fontweight='bold')
        
        # Engagement comparison
        axes[0].barh(df_top['Type'], df_top['Engagement Rate'], color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        axes[0].set_xlabel('Engagement Rate (%)')
        axes[0].set_title('Engagement Rate Comparison')
        
        # Interactions comparison
        x = np.arange(len(df_top))
        width = 0.25
        
        axes[1].bar(x - width, df_top['Likes'], width, label='Likes', color='#FF6B6B')
        axes[1].bar(x, df_top['Comments'], width, label='Comments', color='#4ECDC4')
        axes[1].bar(x + width, df_top['Shares'], width, label='Shares', color='#45B7D1')
        
        axes[1].set_xlabel('Video Type')
        axes[1].set_ylabel('Count')
        axes[1].set_title('Interactions Comparison')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(df_top['Type'], rotation=15)
        axes[1].legend()
        axes[1].ticklabel_format(style='plain', axis='y')
        
        plt.tight_layout()
        file4 = output_path / 'top_videos_comparison.png'
        plt.savefig(file4, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(str(file4))
        print(f"  Đã tạo: {file4.name}")
        
        print(f"\nĐã tạo {len(created_files)} biểu đồ trong thư mục '{output_dir}'")
        
        return {
            'output_directory': str(output_path),
            'created_files': created_files
        }
    
    def generate_report(self, profile_data: Dict, metrics_data: Dict, 
                       sentiment_data: Dict, output_file: str = None) -> str:
        """
        Tạo báo cáo tổng hợp dạng text
        
        Args:
            profile_data: Dữ liệu profile gốc
            metrics_data: Dữ liệu metrics
            sentiment_data: Dữ liệu sentiment
            output_file: Đường dẫn file output (nếu None sẽ chỉ return string)
            
        Returns:
            String chứa báo cáo
        """
        summary = metrics_data['summary']
        trends = metrics_data.get('trends')
        
        report = f"""
{'='*80}
                    YOUTUBE ANALYTICS REPORT
{'='*80}

PROFILE INFORMATION
Username: {summary['username']}
Total Videos Analyzed: {summary['total_videos']}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*80}
 ENGAGEMENT METRICS SUMMARY
{'='*80}

Total Statistics:
  • Total Views: {summary['total_plays']:,}
  • Total Likes: {summary['total_likes']:,}
  • Total Comments: {summary['total_comments']:,}
  • Total Shares: {summary['total_shares']:,}
  • Total Saves: {summary['total_saves']:,}

Average Rates:
  • Engagement Rate: {summary['avg_engagement_rate']:.2f}%
  • Interaction Rate: {summary['avg_interaction_rate']:.2f}%
  • Like Rate: {summary['avg_like_rate']:.2f}%
  • Comment Rate: {summary['avg_comment_rate']:.2f}%
  • Share Rate: {summary['avg_share_rate']:.2f}%
  • Save Rate: {summary['avg_save_rate']:.2f}%
  • Virality Score: {summary['avg_virality_score']:.4f}

Statistical Measures:
  • Median Engagement Rate: {summary['median_engagement_rate']:.2f}%
  • Std Dev Engagement Rate: {summary['std_engagement_rate']:.2f}%

{'='*80}
-----SENTIMENT ANALYSIS SUMMARY-----
{'='*80}

Video Sentiment Distribution:
  • Positive Videos: {sentiment_data['video_sentiment_distribution']['positive']} ({sentiment_data['video_sentiment_percentage']['positive']:.1f}%)
  • Negative Videos: {sentiment_data['video_sentiment_distribution']['negative']} ({sentiment_data['video_sentiment_percentage']['negative']:.1f}%)
  • Neutral Videos: {sentiment_data['video_sentiment_distribution']['neutral']} ({sentiment_data['video_sentiment_percentage']['neutral']:.1f}%)

Comments Sentiment Distribution:
  • Positive Comments: {sentiment_data['comments_sentiment_distribution']['positive']:,} ({sentiment_data['comments_sentiment_percentage']['positive']:.1f}%)
  • Negative Comments: {sentiment_data['comments_sentiment_distribution']['negative']:,} ({sentiment_data['comments_sentiment_percentage']['negative']:.1f}%)
  • Neutral Comments: {sentiment_data['comments_sentiment_distribution']['neutral']:,} ({sentiment_data['comments_sentiment_percentage']['neutral']:.1f}%)
  • Total Comments Analyzed: {sentiment_data['comments_sentiment_distribution']['total']:,}

{'='*80}
----TOP PERFORMING VIDEOS----
{'='*80}
"""
        
        # Add top videos info
        for video_type, video in metrics_data['top_videos'].items():
            report += f"\n{video_type.replace('_', ' ').title()}:\n"
            report += f"  • Video ID: {video['video_id']}\n"
            report += f"  • Engagement Rate: {video['engagement_rate']:.2f}%\n"
            report += f"  • Likes: {video['stats'].get('likes', video['stats'].get('like_count', 0)):,}\n"
            report += f"  • Comments: {video['stats'].get('comments', video['stats'].get('comment_count', 0)):,}\n"
            report += f"  • Shares: {video['stats'].get('shares', video['stats'].get('share_count', 0)):,}\n"
            report += f"  • Plays: {video['stats'].get('plays', video['stats'].get('play_count', 0)):,}\n"
        
        if trends:
            report += f"\n{'='*80}\n"
            report += f" TREND ANALYSIS\n"
            report += f"{'='*80}\n\n"
            report += f"Engagement Trend: {trends['trend'].upper()}\n"
            report += f"  • Early Period Avg: {trends['early_avg_engagement']:.2f}%\n"
            report += f"  • Mid Period Avg: {trends['mid_avg_engagement']:.2f}%\n"
            report += f"  • Recent Period Avg: {trends['recent_avg_engagement']:.2f}%\n"
        
        report += f"\n{'='*80}\n"
        report += f" INSIGHTS & RECOMMENDATIONS\n"
        report += f"{'='*80}\n\n"
        
        # Generate insights
        insights = []
        
        # Engagement insights
        if summary['avg_engagement_rate'] > 5:
            insights.append(" Excellent engagement rate! Your content resonates well with your audience.")
        elif summary['avg_engagement_rate'] > 2:
            insights.append(" Good engagement rate. Consider increasing interaction prompts.")
        else:
            insights.append(" Low engagement rate. Focus on creating more engaging content.")
        
        # Sentiment insights
        if sentiment_data['comments_sentiment_percentage']['positive'] > 60:
            insights.append(" Very positive audience sentiment! Your community loves your content.")
        elif sentiment_data['comments_sentiment_percentage']['negative'] > 30:
            insights.append(" Higher negative sentiment detected. Review audience feedback.")
        
        # Virality insights
        if summary['avg_virality_score'] > 0.01:
            insights.append(" High virality potential! Your content is being shared actively.")
        
        # Share rate insights
        if summary['avg_share_rate'] > 1:
            insights.append(" Strong share rate indicates valuable, shareable content.")
        
        for i, insight in enumerate(insights, 1):
            report += f"{i}. {insight}\n"
        
        report += f"\n{'='*80}\n"
        report += "Report generated by YouTube Analytics AI Module\n"
        report += f"{'='*80}\n"
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f" Đã lưu báo cáo vào: {output_file}")
        
        return report
