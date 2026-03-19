"""Data Exporter - Xuất dữ liệu ra nhiều định dạng

Module này thực hiện bước 5 (cuối cùng) trong pipeline:
- Xuất JSON: dữ liệu đầy đủ dạng gốc
- Xuất CSV: 2 file riêng (videos và comments) dạng Kaggle
- Xuất Excel: file .xlsx với 3 sheet (Videos, Comments, Metadata)
- Xuất Parquet: định dạng nén hiệu quả cho phân tích lớn
"""
import json, csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

class DataExporter:
    """Lớp xuất dữ liệu ra nhiều định dạng khác nhau"""
    
    def __init__(self, output_dir="data/export"):
        """Khởi tạo DataExporter với thư mục đầu ra"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"? DataExporter initialized")
    
    def export_all(self, validated_data, platform, identifier, formats=None):
        """Xuất dữ liệu ra tất cả định dạng được chỉ định
        
        Args:
            validated_data: Dữ liệu đã được xác thực từ bước 4
            platform: Nền tảng (tiktok/youtube)
            identifier: Tên tài khoản
            formats: Danh sách định dạng xuất ['json', 'csv', 'excel', 'parquet']
        """
        if formats is None:
            formats = ['json', 'csv', 'excel', 'parquet']
        
        print(f"\n?? Exporting ({', '.join(formats)})...")
        exported = {}
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if 'json' in formats:
            path = self.output_dir / f"{platform}_{identifier}_{ts}_export.json"
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(validated_data, f, ensure_ascii=False, indent=2)
            exported['json'] = str(path)
            print(f"   ? JSON: {path.name}")
        
        if 'csv' in formats:
            # Xuất Videos CSV (kiểu Kaggle với đầy đủ cột quan trọng)
            videos = validated_data.get('videos', [])
            if videos:
                path_videos = self.output_dir / f"{platform}_{identifier}_{ts}_videos.csv"
                with open(path_videos, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    # Kaggle-style headers with comprehensive columns
                    writer.writerow([
                        'video_id', 'author_name', 'author_id', 'description', 'create_time',
                        'duration', 'music_title', 'music_author', 'hashtags', 'is_ad',
                        'play_count', 'like_count', 'comment_count', 'share_count', 'collect_count',
                        'engagement_rate', 'like_rate', 'comment_rate', 'share_rate',
                        'video_url'
                    ])
                    # Ghi từng dòng video với đầy đủ stats và metrics
                    for v in videos:
                        stats = v.get('stats', {})
                        metrics = v.get('metrics', {})
                        music = v.get('music', {})
                        metadata = v.get('metadata', {})
                        writer.writerow([
                            v.get('id', ''),
                            v.get('author_name', ''),
                            v.get('author_id', ''),
                            v.get('description', ''),
                            v.get('create_time', ''),
                            v.get('duration', ''),
                            music.get('title', ''),
                            music.get('author', ''),
                            '|'.join(v.get('hashtags', [])),
                            v.get('is_ad', False),
                            stats.get('play_count', 0),
                            stats.get('like_count', 0),
                            stats.get('comment_count', 0),
                            stats.get('share_count', 0),
                            stats.get('collect_count', 0),
                            metrics.get('engagement_rate', 0),
                            metrics.get('like_rate', 0),
                            metrics.get('comment_rate', 0),
                            metrics.get('share_rate', 0),
                            v.get('video_url', '')
                        ])
                print(f"   ✅ CSV Videos: {path_videos.name}")
            
            # Xuất Comments CSV (kiểu Kaggle với đầy đủ cột chi tiết)
            comments = validated_data.get('comments', [])
            if comments:
                path_comments = self.output_dir / f"{platform}_{identifier}_{ts}_comments.csv"
                with open(path_comments, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'comment_id', 'video_id', 'text', 'author_name', 'author_id',
                        'author_verified', 'create_time', 'likes', 'reply_count',
                        'is_pinned', 'language', 'sentiment', 'sentiment_confidence',
                        'labeling_method'
                    ])
                    for c in comments:
                        writer.writerow([
                            c.get('id', ''),
                            c.get('video_id', ''),
                            c.get('text', ''),
                            c.get('author_name', ''),
                            c.get('author_id', ''),
                            c.get('author_verified', False),
                            c.get('create_time', ''),
                            c.get('likes', 0),
                            c.get('reply_count', 0),
                            c.get('is_pinned', False),
                            c.get('language', ''),
                            c.get('sentiment', ''),
                            c.get('confidence', 0),
                            c.get('labeling_method', '')
                        ])
                exported['csv'] = {'videos': str(path_videos), 'comments': str(path_comments)}
                print(f"   ✅ CSV Comments: {path_comments.name}")
        
        if 'excel' in formats:
            try:
                path = self.output_dir / f"{platform}_{identifier}_{ts}_dataset.xlsx"
                
                # Tạo DataFrame cho videos và comments
                videos = validated_data.get('videos', [])
                comments = validated_data.get('comments', [])
                
                # Làm phẳng dữ liệu video cho Excel, xử lý Unicode tiếng Việt
                videos_flat = []
                for v in videos:
                    stats = v.get('stats', {})
                    metrics = v.get('metrics', {})
                    music = v.get('music', {})
                    metadata = v.get('metadata', {})
                    
                    # Làm sạch các trường text tiếng Việt (xử lý mã hóa UTF-8)
                    author_name = v.get('author_name', '')
                    if author_name and isinstance(author_name, str):
                        author_name = author_name.encode('utf-8', errors='ignore').decode('utf-8')
                    
                    description = v.get('description', '')
                    if description and isinstance(description, str):
                        description = description.encode('utf-8', errors='ignore').decode('utf-8')
                    
                    music_title = music.get('title', '')
                    if music_title and isinstance(music_title, str):
                        music_title = music_title.encode('utf-8', errors='ignore').decode('utf-8')
                    
                    videos_flat.append({
                        'video_id': v.get('id'),
                        'video_url': v.get('video_url'),
                        'author_name': author_name,
                        'author_id': v.get('author_id'),
                        'description': description,
                        'create_time': v.get('create_time'),
                        'duration': v.get('duration'),
                        'music_title': music_title,
                        'hashtags': '|'.join(v.get('hashtags', [])),
                        'is_ad': v.get('is_ad'),
                        'play_count': stats.get('play_count', 0),
                        'like_count': stats.get('like_count', 0),
                        'comment_count': stats.get('comment_count', 0),
                        'share_count': stats.get('share_count', 0),
                        'collect_count': stats.get('collect_count', 0),
                        'engagement_rate': metrics.get('engagement_rate', 0),
                        'like_rate': metrics.get('like_rate', 0),
                        'comment_rate': metrics.get('comment_rate', 0),
                        'share_rate': metrics.get('share_rate', 0)
                    })
                
                # Làm phẳng dữ liệu comment, xử lý chuỗi Unicode
                comments_flat = []
                for c in comments:
                    # Đảm bảo text được mã hóa đúng UTF-8
                    text = c.get('text', '')
                    if text and isinstance(text, str):
                        # Clean any problematic characters
                        text = text.encode('utf-8', errors='ignore').decode('utf-8')
                    
                    # Xử lý tên tác giả comment
                    author_name = c.get('author_name', '')
                    if author_name and isinstance(author_name, str):
                        author_name = author_name.encode('utf-8', errors='ignore').decode('utf-8')
                    
                    comments_flat.append({
                        'comment_id': c.get('id'),
                        'video_id': c.get('video_id'),
                        'text': text,
                        'author_name': author_name,
                        'author_verified': c.get('author_verified'),
                        'create_time': c.get('create_time'),
                        'likes': c.get('likes'),
                        'reply_count': c.get('reply_count'),
                        'sentiment': c.get('sentiment'),
                        'confidence': c.get('confidence')
                    })
                
                # Ghi Excel với xlsxwriter (định dạng UTF-8 tốt hơn openpyxl)
                with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
                    if videos_flat:
                        df = pd.DataFrame(videos_flat)
                        df.to_excel(writer, sheet_name='Videos', index=False)
                        
                        # Định dạng sheet Videos với độ rộng cột tự động
                        workbook = writer.book
                        worksheet = writer.sheets['Videos']
                        
                        # Create format with text wrapping
                        text_format = workbook.add_format({
                            'text_wrap': True,
                            'valign': 'top',
                            'font_name': 'Arial',
                            'font_size': 10
                        })
                        
                        # Tính độ rộng tối ưu cho mỗi cột
                        for col_num, col_name in enumerate(df.columns):
                            # Tính chiều dài tối đa một cách an toàn
                            try:
                                col_values = df[col_name].fillna('').astype(str)
                                max_len = col_values.str.len().max()
                                max_len = max(max_len, len(str(col_name)))
                                worksheet.set_column(col_num, col_num, min(max_len + 2, 50), text_format)
                            except:
                                worksheet.set_column(col_num, col_num, 15, text_format)
                    
                    if comments_flat:
                        df = pd.DataFrame(comments_flat)
                        df.to_excel(writer, sheet_name='Comments', index=False)
                        
                        # Định dạng sheet Comments
                        workbook = writer.book
                        worksheet = writer.sheets['Comments']
                        
                        # Tạo định dạng text có xuống dòng tự động cho comments
                        text_format = workbook.add_format({
                            'text_wrap': True,
                            'valign': 'top',
                            'font_name': 'Arial',
                            'font_size': 10
                        })
                        
                        # Đặt độ rộng cột phù hợp, cột text rộng hơn
                        for col_num, col_name in enumerate(df.columns):
                            # Xử lý riêng cột text (bình luận) với độ rộng lớn hơn
                            if col_name == 'text':
                                worksheet.set_column(col_num, col_num, 40, text_format)
                            else:
                                try:
                                    col_values = df[col_name].fillna('').astype(str)
                                    max_len = col_values.str.len().max()
                                    max_len = max(max_len, len(str(col_name)))
                                    worksheet.set_column(col_num, col_num, min(max_len + 2, 30), text_format)
                                except:
                                    worksheet.set_column(col_num, col_num, 15, text_format)
                    
                    # Thêm sheet Metadata chứa thông tin tổng quan
                    metadata_df = pd.DataFrame([{
                        'platform': validated_data.get('metadata', {}).get('platform'),
                        'identifier': validated_data.get('metadata', {}).get('identifier'),
                        'collected_at': validated_data.get('metadata', {}).get('collected_at'),
                        'total_videos': len(videos),
                        'total_comments': len(comments)
                    }])
                    metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
                    
                    # Định dạng sheet Metadata
                    workbook = writer.book
                    worksheet = writer.sheets['Metadata']
                    text_format = workbook.add_format({
                        'font_name': 'Arial',
                        'font_size': 10
                    })
                    
                    for col_num, col_name in enumerate(metadata_df.columns):
                        try:
                            col_values = metadata_df[col_name].fillna('').astype(str)
                            max_len = col_values.str.len().max()
                            max_len = max(max_len, len(str(col_name)))
                            worksheet.set_column(col_num, col_num, min(max_len + 2, 30), text_format)
                        except:
                            worksheet.set_column(col_num, col_num, 20, text_format)
                
                exported['excel'] = str(path)
                print(f"   ✅ Excel: {path.name}")
            except Exception as e:
                print(f"   ⚠️  Excel export failed: {e}")
        
        if 'parquet' in formats:
            try:
                # Xuất Videos dạng Parquet (định dạng cột, nén hiệu quả)
                videos = validated_data.get('videos', [])
                if videos:
                    videos_flat = []
                    for v in videos:
                        stats = v.get('stats', {})
                        metrics = v.get('metrics', {})
                        music = v.get('music', {})
                        metadata = v.get('metadata', {})
                        videos_flat.append({
                            'video_id': v.get('id'),
                            'author_name': v.get('author_name'),
                            'author_id': v.get('author_id'),
                            'description': v.get('description'),
                            'create_time': v.get('create_time'),
                            'duration': v.get('duration'),
                            'music_title': music.get('title'),
                            'hashtags': '|'.join(v.get('hashtags', [])),
                            'is_ad': v.get('is_ad'),
                            'play_count': stats.get('play_count'),
                            'like_count': stats.get('like_count'),
                            'comment_count': stats.get('comment_count'),
                            'share_count': stats.get('share_count'),
                            'engagement_rate': metrics.get('engagement_rate')
                        })
                    
                    path = self.output_dir / f"{platform}_{identifier}_{ts}_videos.parquet"
                    df = pd.DataFrame(videos_flat)
                    df.to_parquet(path, compression='snappy', index=False)
                    print(f"   ✅ Parquet Videos: {path.name}")
                
                # Xuất Comments dạng Parquet
                comments = validated_data.get('comments', [])
                if comments:
                    path = self.output_dir / f"{platform}_{identifier}_{ts}_comments.parquet"
                    df = pd.DataFrame(comments)
                    df.to_parquet(path, compression='snappy', index=False)
                    exported['parquet'] = {'comments': str(path)}
                    print(f"   ✅ Parquet Comments: {path.name}")
            except Exception as e:
                print(f"   ⚠️  Parquet export failed: {e}")
        
        print(f"? Export complete!")
        return exported
