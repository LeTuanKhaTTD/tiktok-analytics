"""
============================================================================
VISUALIZE SENTIMENT ANALYSIS - TẠO BÁO CÁO SẮC THÁI
============================================================================

Script để tạo visualizations và insights từ sentiment analysis có sẵn

USAGE:
python visualize_sentiment.py data/tiktok_travinhuniversity_20260303_133551_sentiment.json

============================================================================
"""
import json
import sys
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend cho server
import os
from datetime import datetime

# Set font for Vietnamese
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['axes.unicode_minus'] = False

def load_sentiment_data(filepath):
    """Load sentiment JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_sentiment_pie_chart(sentiment_summary, output_dir):
    """Tạo pie chart cho sentiment distribution"""
    labels = ['Positive (Tích cực)', 'Neutral (Trung lập)', 'Negative (Tiêu cực)']
    sizes = [
        sentiment_summary['positive']['count'],
        sentiment_summary['neutral']['count'],
        sentiment_summary['negative']['count']
    ]
    colors = ['#4CAF50', '#FFC107', '#F44336']
    explode = (0.1, 0, 0)  # Explode positive
    
    plt.figure(figsize=(10, 7))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=90)
    plt.title('Phân bố Sắc thái Comments (Sentiment Distribution)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.axis('equal')
    
    filepath = os.path.join(output_dir, 'sentiment_distribution.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Saved: {filepath}")
    return filepath

def create_sentiment_bar_chart(sentiment_summary, output_dir):
    """Tạo bar chart so sánh sentiment counts"""
    categories = ['Positive', 'Neutral', 'Negative']
    counts = [
        sentiment_summary['positive']['count'],
        sentiment_summary['neutral']['count'],
        sentiment_summary['negative']['count']
    ]
    colors = ['#4CAF50', '#FFC107', '#F44336']
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(categories, counts, color=colors, alpha=0.8, edgecolor='black')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    plt.title('Số lượng Comments theo Sắc thái', fontsize=16, fontweight='bold')
    plt.xlabel('Sentiment', fontsize=12)
    plt.ylabel('Số lượng comments', fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    
    filepath = os.path.join(output_dir, 'sentiment_counts.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Saved: {filepath}")
    return filepath

def analyze_top_comments(comments, output_dir):
    """Phân tích top comments theo likes và sentiment"""
    # Sort by likes
    sorted_comments = sorted(comments, key=lambda x: x.get('likes', 0), reverse=True)
    top_10 = sorted_comments[:10]
    
    # Create visualization
    plt.figure(figsize=(12, 8))
    
    sentiments = [c['sentiment'] for c in top_10]
    likes = [c.get('likes', 0) for c in top_10]
    colors_map = {'positive': '#4CAF50', 'neutral': '#FFC107', 'negative': '#F44336'}
    colors = [colors_map[s] for s in sentiments]
    
    y_pos = range(len(top_10))
    
    plt.barh(y_pos, likes, color=colors, alpha=0.8, edgecolor='black')
    
    # Truncate text for labels
    labels = [c['text'][:40] + '...' if len(c['text']) > 40 else c['text'] 
              for c in top_10]
    
    plt.yticks(y_pos, labels, fontsize=9)
    plt.xlabel('Số lượt thích (Likes)', fontsize=12)
    plt.title('Top 10 Comments có nhiều Likes nhất', fontsize=14, fontweight='bold')
    plt.grid(axis='x', alpha=0.3)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#4CAF50', label='Positive'),
        Patch(facecolor='#FFC107', label='Neutral'),
        Patch(facecolor='#F44336', label='Negative')
    ]
    plt.legend(handles=legend_elements, loc='lower right')
    
    filepath = os.path.join(output_dir, 'top_comments_by_likes.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Saved: {filepath}")
    return filepath

def analyze_video_sentiment(comments, output_dir):
    """Phân tích sentiment theo từng video"""
    video_sentiments = {}
    
    for comment in comments:
        video_id = comment.get('video_id', 'unknown')
        sentiment = comment.get('sentiment', 'neutral')
        
        if video_id not in video_sentiments:
            video_sentiments[video_id] = {'positive': 0, 'neutral': 0, 'negative': 0}
        
        video_sentiments[video_id][sentiment] += 1
    
    # Take top 10 videos by total comments
    video_data = []
    for vid, sents in video_sentiments.items():
        total = sum(sents.values())
        video_data.append({
            'id': vid,
            'total': total,
            'positive': sents['positive'],
            'neutral': sents['neutral'],
            'negative': sents['negative']
        })
    
    video_data = sorted(video_data, key=lambda x: x['total'], reverse=True)[:10]
    
    # Create stacked bar chart
    if not video_data:
        print("   ⚠️  Not enough video data for visualization")
        return None
    
    video_labels = [f"Video {v['id'][-4:]}" for v in video_data]
    positive = [v['positive'] for v in video_data]
    neutral = [v['neutral'] for v in video_data]
    negative = [v['negative'] for v in video_data]
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    x = range(len(video_labels))
    width = 0.6
    
    p1 = ax.bar(x, positive, width, label='Positive', color='#4CAF50', alpha=0.8)
    p2 = ax.bar(x, neutral, width, bottom=positive, label='Neutral', color='#FFC107', alpha=0.8)
    p3 = ax.bar(x, negative, width, bottom=[i+j for i,j in zip(positive, neutral)], 
                label='Negative', color='#F44336', alpha=0.8)
    
    ax.set_xlabel('Videos', fontsize=12)
    ax.set_ylabel('Số lượng comments', fontsize=12)
    ax.set_title('Phân bố Sentiment theo từng Video (Top 10)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(video_labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    filepath = os.path.join(output_dir, 'sentiment_by_video.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Saved: {filepath}")
    return filepath

def generate_insights(sentiment_summary, comments, total_comments):
    """Tạo insights và recommendations từ sentiment data"""
    
    positive_pct = sentiment_summary['positive']['percentage']
    negative_pct = sentiment_summary['negative']['percentage']
    neutral_pct = sentiment_summary['neutral']['percentage']
    
    insights = []
    recommendations = []
    
    # Insight 1: Overall sentiment
    if positive_pct > 40:
        insights.append("✅ **Tích cực cao**: Audience có phản ứng positive mạnh với nội dung")
        recommendations.append("💡 Tiếp tục duy trì style và chủ đề hiện tại")
    elif positive_pct > 30:
        insights.append("📊 **Cân bằng tốt**: Sentiment distribution khá healthy")
    else:
        insights.append("⚠️ **Positive thấp**: Cần cải thiện nội dung để tăng engagement positive")
        recommendations.append("💡 Tạo nội dung inspiring, educational hơn để tăng positive sentiment")
    
    # Insight 2: Negative sentiment
    if negative_pct > 25:
        insights.append("❌ **Negative cao**: Có vấn đề cần giải quyết với audience")
        recommendations.append("💡 Đọc kỹ negative comments để hiểu pain points của audience")
        recommendations.append("💡 Tạo video Q&A hoặc giải thích để address concerns")
    elif negative_pct < 15:
        insights.append("✅ **Negative thấp**: Audience hài lòng với nội dung")
    
    # Insight 3: Neutral sentiment
    if neutral_pct > 50:
        insights.append("⚪ **Neutral cao**: Comments thiếu emotional engagement")
        recommendations.append("💡 Tạo nội dung provocative hơn để trigger emotional response")
        recommendations.append("💡 Thêm call-to-action trong video để encourage discussion")
    
    # Insight 4: Top comments analysis
    top_comments = sorted(comments, key=lambda x: x.get('likes', 0), reverse=True)[:5]
    top_positive = sum(1 for c in top_comments if c['sentiment'] == 'positive')
    
    if top_positive >= 3:
        insights.append("🔥 **Top comments positive**: Viral potential cao, audience engage tốt")
    elif any(c['sentiment'] == 'negative' and c.get('likes', 0) > 20 for c in top_comments):
        insights.append("⚠️ **Negative viral**: Có negative comment được like nhiều - cần xử lý")
        recommendations.append("💡 Reply và giải quyết negative comments có engagement cao")
    
    # Insight 5: Engagement quality
    avg_confidence = sum(c.get('confidence', 0) for c in comments) / len(comments) if comments else 0
    if avg_confidence > 0.6:
        insights.append("💪 **High confidence**: Sentiment rõ ràng, audience có ý kiến mạnh mẽ")
    
    return insights, recommendations

def create_report(sentiment_summary, comments, total_comments, output_dir):
    """Tạo text report"""
    
    report_lines = []
    report_lines.append("="*80)
    report_lines.append(" BÁO CÁO PHÂN TÍCH SẮC THÁI COMMENTS - SENTIMENT ANALYSIS REPORT")
    report_lines.append("="*80)
    report_lines.append("")
    
    # Summary stats
    report_lines.append("📊 TỔNG QUAN - SUMMARY")
    report_lines.append("-" * 80)
    report_lines.append(f"Tổng số comments phân tích: {total_comments}")
    report_lines.append("")
    report_lines.append(f"✅ Positive (Tích cực):  {sentiment_summary['positive']['count']:3d} comments "
                       f"({sentiment_summary['positive']['percentage']:.1f}%)")
    report_lines.append(f"⚪ Neutral (Trung lập):  {sentiment_summary['neutral']['count']:3d} comments "
                       f"({sentiment_summary['neutral']['percentage']:.1f}%)")
    report_lines.append(f"❌ Negative (Tiêu cực): {sentiment_summary['negative']['count']:3d} comments "
                       f"({sentiment_summary['negative']['percentage']:.1f}%)")
    report_lines.append("")
    
    # Insights
    insights, recommendations = generate_insights(sentiment_summary, comments, total_comments)
    
    report_lines.append("💡 INSIGHTS - PHÂN TÍCH CHUYÊN SÂU")
    report_lines.append("-" * 80)
    for insight in insights:
        report_lines.append(f"  {insight}")
    report_lines.append("")
    
    # Recommendations
    report_lines.append("🎯 RECOMMENDATIONS - ĐỀ XUẤT CẢI THIỆN")
    report_lines.append("-" * 80)
    for rec in recommendations:
        report_lines.append(f"  {rec}")
    report_lines.append("")
    
    # Top positive comments
    positive_comments = [c for c in comments if c['sentiment'] == 'positive']
    if positive_comments:
        top_positive = sorted(positive_comments, key=lambda x: x.get('likes', 0), reverse=True)[:3]
        report_lines.append("🌟 TOP POSITIVE COMMENTS")
        report_lines.append("-" * 80)
        for i, c in enumerate(top_positive, 1):
            report_lines.append(f"{i}. \"{c['text'][:80]}{'...' if len(c['text']) > 80 else ''}\"")
            report_lines.append(f"   👍 {c.get('likes', 0)} likes | Confidence: {c.get('confidence', 0):.2f}")
            report_lines.append("")
    
    # Top negative comments (to address)
    negative_comments = [c for c in comments if c['sentiment'] == 'negative']
    if negative_comments:
        top_negative = sorted(negative_comments, key=lambda x: x.get('likes', 0), reverse=True)[:3]
        report_lines.append("⚠️  TOP NEGATIVE COMMENTS (CẦN XỬ LÝ)")
        report_lines.append("-" * 80)
        for i, c in enumerate(top_negative, 1):
            report_lines.append(f"{i}. \"{c['text'][:80]}{'...' if len(c['text']) > 80 else ''}\"")
            report_lines.append(f"   👍 {c.get('likes', 0)} likes | Confidence: {c.get('confidence', 0):.2f}")
            report_lines.append("")
    
    report_lines.append("="*80)
    report_lines.append(f" Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("="*80)
    
    # Save to file
    report_text = "\n".join(report_lines)
    filepath = os.path.join(output_dir, 'sentiment_report.txt')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"   ✅ Saved: {filepath}")
    
    # Also print to console
    print("\n" + report_text)
    
    return filepath

def main():
    """Main function"""
    print("="*80)
    print(" SENTIMENT ANALYSIS VISUALIZER")
    print("="*80)
    print()
    
    # Get file path
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = "data/tiktok_travinhuniversity_20260303_133551_sentiment.json"
        print(f"Using default file: {filepath}")
    
    # Check if file exists
    if not os.path.exists(filepath):
        print(f"❌ Error: File not found: {filepath}")
        print("Usage: python visualize_sentiment.py <path_to_sentiment_json>")
        return
    
    # Load data
    print(f"📂 Loading data from: {filepath}")
    data = load_sentiment_data(filepath)
    print(f"   ✅ Loaded {data['total_comments']} comments")
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"reports/sentiment_analysis_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    print()
    
    # Handle both organized (videos[]) and flat (comments[]) structures
    if 'videos' in data and 'global_sentiment_summary' in data:
        # Organized structure - flatten it
        print("📦 Detected organized structure (by video), flattening for visualization...")
        sentiment_summary = data['global_sentiment_summary']
        all_comments = []
        for video in data['videos']:
            all_comments.extend(video.get('comments', []))
        comments = all_comments
        print(f"   ✅ Flattened {len(comments)} comments from {len(data['videos'])} videos")
        print()
    else:
        # Flat structure
        sentiment_summary = data['sentiment_summary']
        comments = data['comments']
    
    # Generate visualizations
    print("🎨 Creating visualizations...")
    print()
    
    create_sentiment_pie_chart(sentiment_summary, output_dir)
    create_sentiment_bar_chart(sentiment_summary, output_dir)
    analyze_top_comments(comments, output_dir)
    analyze_video_sentiment(comments, output_dir)
    
    print()
    
    # Generate text report
    print("📝 Generating report...")
    print()
    create_report(sentiment_summary, comments, len(comments), output_dir)
    
    print()
    print("="*80)
    print(" ✅ COMPLETED!")
    print("="*80)
    print(f"\n📁 All outputs saved in: {output_dir}")
    print()
    print("Files created:")
    print("  - sentiment_distribution.png")
    print("  - sentiment_counts.png")
    print("  - top_comments_by_likes.png")
    print("  - sentiment_by_video.png")
    print("  - sentiment_report.txt")
    print()

if __name__ == "__main__":
    main()
