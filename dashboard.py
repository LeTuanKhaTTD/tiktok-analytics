"""
Dashboard TikTok Analytics - @travinhuniversity
Công cụ trực quan hóa và gán nhãn sentiment bình luận

Chạy: streamlit run dashboard.py
"""

import json
import os
import io
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# Import config và modules
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_ENABLE_CACHE, GEMINI_MAX_RETRIES, GEMINI_BASE_DELAY
from modules.gemini_sentiment import GeminiSentimentAnalyzer, get_gemini_analyzer
try:
    from modules.text_preprocessor import TextPreprocessor, basic_clean_text, preprocess, is_low_value, TEENCODE_DICT, EMOJI_SENTIMENT
    _PREPROCESSOR_OK = True
except ImportError:
    _PREPROCESSOR_OK = False

try:
    from modules.phobert_sentiment import PhoBERTSentiment, is_model_available, get_model_path
    _PHOBERT_IMPORTABLE = True
except ImportError:
    _PHOBERT_IMPORTABLE = False
    def is_model_available(): return False
    def get_model_path(): return None

# Đảm bảo CWD là thư mục chứa dashboard.py
os.chdir(Path(__file__).parent)

# ========== GEMINI SENTIMENT FUNCTIONS ==========

# Lấy API key từ config hoặc environment variable
_GEMINI_API_KEY = GEMINI_API_KEY or os.getenv('GEMINI_API_KEY') or "AIzaSyB3b12woY37mDHvq_R4aKEhuaNESoMcC4s"

def get_gemini_analyzer_singleton():
    """Khởi tạo và lấy Gemini Analyzer singleton"""
    if 'gemini_analyzer' not in st.session_state:
        st.session_state.gemini_analyzer = get_gemini_analyzer(_GEMINI_API_KEY)
    return st.session_state.gemini_analyzer

def gemini_analyze_single(text: str, analyzer: GeminiSentimentAnalyzer = None) -> tuple[str, float]:
    """Phân tích sentiment cho 1 comment"""
    if analyzer is None:
        analyzer = get_gemini_analyzer_singleton()
    
    return analyzer.analyze_sentiment(text)

def gemini_batch_label(comments: list, show_stats: bool = True) -> int:
    """Gán nhãn hàng loạt cho comments chưa có nhãn thủ công"""
    analyzer = get_gemini_analyzer_singleton()
    
    # Lọc comments cần xử lý
    to_process = [
        c for c in comments
        if str(c.get("method", "")).strip().lower() != "manual"
    ]
    
    if not to_process:
        st.info("Không có comment nào cần gán nhãn tự động.")
        return 0
    
    total = len(to_process)
    updated = 0
    
    # Progress bar
    progress_bar = st.progress(0, text="Đang chuẩn bị...")
    status_text = st.empty()
    
    # Batch processing với callback
    def progress_callback(current, total, message):
        nonlocal updated
        progress_bar.progress(current / total, text=f"Đang xử lý {current}/{total}")
        status_text.text(message)
    
    try:
        # Analyze
        texts = [c["text"] for c in to_process]
        results = analyzer.batch_analyze(texts, progress_callback=progress_callback)

        update_map = {}
        for comment, result in zip(to_process, results):
            update_map[_comment_key(comment)] = {
                "sentiment": result["sentiment"],
                "confidence": result["confidence"],
                "method": "gemini",
            }

        updated = _persist_prediction_updates(update_map, comments_ref=comments)
        
        progress_bar.empty()
        status_text.empty()
        
        # Hiển thị statistics
        if show_stats:
            stats = analyzer.get_statistics()
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📊 Tổng requests", stats["total_requests"])
            col2.metric("✅ Cache hits", stats["cache_hits"])
            col3.metric("🌐 API calls", stats["api_calls"])
            col4.metric("💾 Cache hit rate", f"{stats['cache_hit_rate']:.1f}%")
        
        return updated
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Lỗi khi phân tích: {e}")
        return 0

# ========== END GEMINI SENTIMENT FUNCTIONS ==========

# ============================================================================
# CẤU HÌNH
# ============================================================================
MERGED_FILE = Path("data/merged/tiktok_travinhuniversity_merged.json")
COMMENT_FILE = Path("data/tong_hop_comment.json")
EXPORT_DIR = Path("data/export")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
VALID_SENTIMENTS = ("positive", "neutral", "negative")

st.set_page_config(
    page_title="TikTok Analytics - TVU",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# TẢI DỮ LIỆU
# ============================================================================
@st.cache_data
def load_data(merged_mtime_ns: int | None = None):
    """Tải dữ liệu từ file merged JSON"""
    _ = merged_mtime_ns
    if MERGED_FILE.exists():
        with open(MERGED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        # Fallback cho môi trường cloud khi file merged chưa được đưa lên repo.
        source = load_comment_source()
        data = _build_data_from_comment_source(source)
        data.setdefault("metadata", {})["fallback"] = "loaded_from_comment_file"

        # Tự tạo merged file để các lần chạy sau dùng lại dữ liệu ổn định hơn.
        try:
            MERGED_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(MERGED_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            # Trên một số môi trường cloud có thể không cho ghi; vẫn tiếp tục chạy fallback.
            pass

    videos = data.get("videos", [])
    comments = data.get("comments", [])
    metadata = data.get("metadata", {})
    user = data.get("user", {})
    return videos, comments, metadata, user


def load_comment_source():
    """Tải file tong_hop_comment.json (nguồn gốc comment + sentiment)"""
    if not COMMENT_FILE.exists():
        return {"videos": []}
    with open(COMMENT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_data_from_comment_source(source: dict) -> dict:
    """Chuẩn hóa dữ liệu kiểu tong_hop_comment.json thành cấu trúc dashboard."""
    videos = source.get("videos", [])
    comments = []
    for video in videos:
        comments.extend(video.get("comments", []))

    return {
        "videos": videos,
        "comments": comments,
        "metadata": {
            "source": source.get("source", "uploaded"),
            "total_videos": source.get("total_videos", len(videos)),
            "total_comments": source.get("total_comments", len(comments)),
            "fallback": "loaded_from_uploaded_file",
        },
        "user": {
            "username": source.get("username", "@unknown"),
        },
    }


def _parse_uploaded_dataset(uploaded_file):
    """Đọc dataset upload (JSON/CSV) và trả về cấu trúc data chuẩn cho dashboard."""
    filename = str(getattr(uploaded_file, "name", "")).lower()

    if filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        comments = df.to_dict(orient="records")
        return {
            "videos": [],
            "comments": comments,
            "metadata": {
                "source": "uploaded_csv",
                "total_videos": 0,
                "total_comments": len(comments),
                "fallback": "loaded_from_uploaded_file",
            },
            "user": {"username": "@uploaded"},
        }

    payload = json.load(uploaded_file)

    # merged format
    if isinstance(payload, dict) and ("videos" in payload or "comments" in payload):
        has_merged_shape = isinstance(payload.get("comments", []), list) and isinstance(payload.get("videos", []), list)
        if has_merged_shape and ("metadata" in payload or "user" in payload):
            payload.setdefault("metadata", {})
            payload.setdefault("user", {"username": "@uploaded"})
            payload["metadata"].setdefault("fallback", "loaded_from_uploaded_file")
            return payload

        # tong_hop_comment format
        return _build_data_from_comment_source(payload)

    raise ValueError("Dinh dang file khong duoc ho tro.")


def _get_runtime_data(default_data: tuple[list, list, dict, dict]) -> tuple[list, list, dict, dict]:
    """Ưu tiên dữ liệu upload trong session cho môi trường cloud không có data file."""
    uploaded_data = st.session_state.get("uploaded_runtime_data")
    if not uploaded_data:
        return default_data
    return (
        uploaded_data.get("videos", []),
        uploaded_data.get("comments", []),
        uploaded_data.get("metadata", {}),
        uploaded_data.get("user", {}),
    )


def save_comment_source(data):
    """Lưu lại file tong_hop_comment.json sau khi sửa nhãn"""
    with open(COMMENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _norm_text(text) -> str:
    """Chuẩn hóa text để so khớp ổn định khi lưu nhãn thủ công."""
    if text is None:
        return ""
    return str(text).strip()


def _normalize_sentiment_value(value: str) -> str:
    """Chuẩn hóa sentiment; giá trị rỗng được xem là unlabeled."""
    sent = str(value or "").strip().lower()
    return sent if sent else "unlabeled"


def _prepare_comments_df(comments: list) -> pd.DataFrame:
    """Chuẩn hóa DataFrame comment để toàn dashboard dùng chung một quy tắc."""
    df_c = pd.DataFrame(comments)
    if df_c.empty:
        return df_c

    if "sentiment" not in df_c.columns:
        df_c["sentiment"] = "unlabeled"
    else:
        df_c["sentiment"] = df_c["sentiment"].apply(_normalize_sentiment_value)

    if "confidence" not in df_c.columns:
        df_c["confidence"] = 0.0
    df_c["confidence"] = pd.to_numeric(df_c["confidence"], errors="coerce").fillna(0.0)

    if "method" not in df_c.columns:
        df_c["method"] = ""
    df_c["method"] = df_c["method"].fillna("").astype(str).str.strip().str.lower()

    return df_c


def _labeled_comments_df(df_c: pd.DataFrame) -> pd.DataFrame:
    """Chỉ lấy comment đã có sentiment hợp lệ."""
    if df_c.empty or "sentiment" not in df_c.columns:
        return pd.DataFrame()
    return df_c[df_c["sentiment"].isin(VALID_SENTIMENTS)].copy()


def _comment_key(comment: dict) -> tuple[str, str, str, str, str]:
    """Khóa ổn định để đồng bộ một comment giữa UI, merged file và source file."""
    return (
        str(comment.get("video_id", "")).strip(),
        _norm_text(comment.get("text", "")),
        str(comment.get("author", "")).strip().lower(),
        str(comment.get("created_at", "")).strip(),
        str(comment.get("cid", "")).strip(),
    )


def _apply_prediction_updates(comments_list: list, updates: dict, touched_keys: set | None = None) -> int:
    """Áp dụng nhãn dự đoán vào danh sách comment, bỏ qua nhãn thủ công."""
    applied = 0
    for comment in comments_list:
        key = _comment_key(comment)
        if key not in updates:
            continue
        if str(comment.get("method", "")).strip().lower() == "manual":
            continue

        update = updates[key]
        comment["sentiment"] = update["sentiment"]
        comment["confidence"] = update["confidence"]
        comment["method"] = update["method"]
        applied += 1
        if touched_keys is not None:
            touched_keys.add(key)
    return applied


def _persist_prediction_updates(updates: dict, comments_ref: list | None = None) -> int:
    """Lưu nhãn dự đoán vào source file, merged file và dữ liệu đang hiển thị."""
    touched_keys: set[tuple[str, str, str, str, str]] = set()

    comment_data = load_comment_source()
    for video in comment_data.get("videos", []):
        _apply_prediction_updates(video.get("comments", []), updates, touched_keys)
    save_comment_source(comment_data)

    if MERGED_FILE.exists():
        with open(MERGED_FILE, "r", encoding="utf-8") as f:
            merged = json.load(f)

        _apply_prediction_updates(merged.get("comments", []), updates)
        for video in merged.get("videos", []):
            _apply_prediction_updates(video.get("comments", []), updates)

        with open(MERGED_FILE, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

    if comments_ref is not None:
        _apply_prediction_updates(comments_ref, updates)

    return len(touched_keys)


# ============================================================================
# SIDEBAR - ĐIỀU HƯỚNG
# ============================================================================
def sidebar():
    with st.sidebar:
        st.markdown(
            """
            <style>
            section[data-testid="stSidebar"] .block-container {
                padding-top: 0.75rem;
                padding-bottom: 0.75rem;
            }
            section[data-testid="stSidebar"] hr {
                margin-top: 0.6rem;
                margin-bottom: 0.6rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # ── Logo TVU ─────────────────────────────────────────────────────────
        _logo_path = Path(__file__).parent / "assets" / "logo_tvu.png"
        _logo_candidates = [
            _logo_path,
            Path(__file__).parent / "assets" / "logo_tvu.jpg",
            Path(__file__).parent / "assets" / "logo.png",
            Path(__file__).parent / "assets" / "logo.jpg",
        ]
        _logo_found = next((p for p in _logo_candidates if p.exists()), None)

        st.markdown("""
            <div style='text-align:center; padding: 2px 0 2px 0;'>
                <span style='font-size:12px; color:#888; letter-spacing:1px;'>TRƯỜNG ĐẠI HỌC TRÀ VINH</span>
            </div>
        """, unsafe_allow_html=True)

        _sp1, _logo_col, _sp2 = st.columns([1, 2, 1])
        with _logo_col:
            if _logo_found:
                st.image(str(_logo_found), width=120)
            else:
                st.image("https://www.tvu.edu.vn/wp-content/uploads/2020/03/logo-TVU-1.png", width=120)

        st.markdown("""
            <div style='text-align:center; padding: 2px 0 2px 0;'>
                <span style='font-size:14px; font-weight:700; color:#1a73e8;'>TikTok Analytics</span><br>
                <span style='font-size:10px; color:#aaa;'>@travinhuniversity</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation
        page = st.radio(
            "Điều hướng",
            [
                "Tổng quan",
                "Sentiment theo Video",
                "Chi tiết bình luận",
                "Gán nhãn thủ công",
                "Xuất / Nhập Excel",
                "Đánh giá Gemini",
                "Phân tích Chủ đề & Viral",
                "Tiền xử lý Text",
                "PhoBERT Fine-tuned",
            ],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Quick stats trong sidebar
        st.subheader("Quick Stats")
        try:
            merged_mtime = MERGED_FILE.stat().st_mtime_ns if MERGED_FILE.exists() else None
            videos, comments, _, _ = load_data(merged_mtime)
            df_c = _prepare_comments_df(comments)
            df_labeled = _labeled_comments_df(df_c)
            
            st.metric("Videos", len(videos))
            st.metric("Comments", len(comments))
            st.metric("Labeled", len(df_labeled))
            st.metric("Unlabeled", int((df_c["sentiment"] == "unlabeled").sum()) if not df_c.empty else 0)
            
            if not df_labeled.empty:
                pos_pct = (df_labeled["sentiment"] == "positive").sum() / len(df_labeled) * 100
                st.caption(f"Positive rate (labeled): {pos_pct:.1f}%")
        except:
            pass
        
        st.divider()
        
        # Info
        st.caption("**Tips:**")
        st.caption("- Dùng Gemini để phân tích tự động")
        st.caption("- Gán nhãn thủ công cho độ chính xác cao")
        st.caption("- Xuất Excel để xử lý offline")
        
        st.divider()
        st.caption("Version: 2.0")
        st.caption("Updated: 2026-03-16")
    
    return page


# ============================================================================
# TRANG 1: TỔNG QUAN
# ============================================================================
def page_overview(videos, comments, metadata, user):
    st.title("Tổng quan TikTok Analytics")
    st.caption("Dashboard phân tích tương tác và cảm xúc người dùng TikTok")

    # --- KPI Cards ---
    df_c = _prepare_comments_df(comments)
    df_labeled = _labeled_comments_df(df_c)

    total_plays = sum(v.get("stats", {}).get("play_count", 0) for v in videos)
    total_likes = sum(v.get("stats", {}).get("like_count", 0) for v in videos)
    total_shares = sum(
        v.get("stats", {}).get("share_count", 0) for v in videos
    )
    total_saves = sum(
        v.get("stats", {}).get("collect_count", 0) for v in videos
    )
    total_comments_collected = len(comments)
    
    # Tính engagement rate trung bình
    avg_engagement = 0
    if total_plays > 0:
        avg_engagement = ((total_likes + total_comments_collected + total_shares) / total_plays) * 100

    st.subheader("📊 Metrics Tổng quan")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    col1.metric("🎬 Videos", f"{len(videos)}", help="Tổng số video đã phân tích")
    col2.metric("👁️ Views", f"{total_plays:,}", help="Tổng lượt xem")
    col3.metric("❤️ Likes", f"{total_likes:,}", help="Tổng lượt thích")
    col4.metric("💬 Comments", f"{total_comments_collected:,}", help="Tổng bình luận thu thập")
    col5.metric("🔗 Shares", f"{total_shares:,}", help="Tổng lượt chia sẻ")
    col6.metric("📈 Engagement", f"{avg_engagement:.2f}%", help="Tỷ lệ tương tác trung bình")

    st.divider()
    
    # --- Sentiment Overview ---
    st.subheader("😊 Phân tích Sentiment")
    
    if not df_c.empty and "sentiment" in df_c.columns:
        col_sent1, col_sent2, col_sent3, col_sent4 = st.columns(4)

        labeled_total = len(df_labeled)
        positive_count = int((df_labeled["sentiment"] == "positive").sum()) if labeled_total else 0
        neutral_count = int((df_labeled["sentiment"] == "neutral").sum()) if labeled_total else 0
        negative_count = int((df_labeled["sentiment"] == "negative").sum()) if labeled_total else 0
        unlabeled_count = int((df_c["sentiment"] == "unlabeled").sum())

        if labeled_total:
            col_sent1.metric("✅ Positive", f"{positive_count}", f"{positive_count/labeled_total*100:.1f}%")
            col_sent2.metric("⚪ Neutral", f"{neutral_count}", f"{neutral_count/labeled_total*100:.1f}%")
            col_sent3.metric("❌ Negative", f"{negative_count}", f"{negative_count/labeled_total*100:.1f}%")
            col_sent4.metric("🎯 Coverage", f"{labeled_total/len(df_c)*100:.1f}%", f"{unlabeled_count} unlabeled")
            st.caption("Sentiment KPI được tính trên phần comment đã có nhãn; coverage phản ánh mức sẵn sàng để phân tích/train.")
        else:
            col_sent1.metric("✅ Positive", "0")
            col_sent2.metric("⚪ Neutral", "0")
            col_sent3.metric("❌ Negative", "0")
            col_sent4.metric("🎯 Coverage", "0.0%", f"{unlabeled_count} unlabeled")

    st.divider()

    # --- Biểu đồ sentiment ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📊 Phân phối Sentiment")
        if not df_labeled.empty:
            counts = df_labeled["sentiment"].value_counts()
            fig_pie = px.pie(
                values=counts.values,
                names=counts.index,
                color=counts.index,
                color_discrete_map={
                    "positive": "#2ecc71",
                    "neutral": "#3498db",
                    "negative": "#e74c3c",
                },
                hole=0.4,
            )
            fig_pie.update_traces(textinfo="percent+label+value", textfont_size=14)
            fig_pie.update_layout(height=450, showlegend=True, 
                                 legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("📈 Phân bổ Confidence Score")
        if not df_labeled.empty and "confidence" in df_labeled.columns:
            fig_hist = px.histogram(
                df_labeled,
                x="confidence",
                color="sentiment",
                nbins=30,
                color_discrete_map={
                    "positive": "#2ecc71",
                    "neutral": "#3498db",
                    "negative": "#e74c3c",
                },
                barmode="overlay",
                opacity=0.7,
            )
            fig_hist.add_vline(x=0.7, line_dash="dash", line_color="gray",
                               annotation_text="Ngưỡng 0.7", annotation_position="top")
            fig_hist.update_layout(height=450, xaxis_title="Confidence", yaxis_title="Số lượng")
            st.plotly_chart(fig_hist, use_container_width=True)
    
    st.divider()

    # --- Top 10 video nhiều views ---
    st.subheader("🏆 Top 10 Video xuất sắc nhất")
    
    tab1, tab2, tab3 = st.tabs(["👁️ Nhiều views nhất", "❤️ Nhiều likes nhất", "💬 Nhiều comments nhất"])
    
    with tab1:
        top_videos = sorted(
            videos,
            key=lambda v: v.get("stats", {}).get("play_count", 0),
            reverse=True,
        )[:10]
        _display_video_table(top_videos, "Views")
    
    with tab2:
        top_videos = sorted(
            videos,
            key=lambda v: v.get("stats", {}).get("like_count", 0),
            reverse=True,
        )[:10]
        _display_video_table(top_videos, "Likes")
    
    with tab3:
        top_videos = sorted(
            videos,
            key=lambda v: v.get("stats", {}).get("comment_count", 0),
            reverse=True,
        )[:10]
        _display_video_table(top_videos, "Comments")

def _display_video_table(top_videos, sort_by):
    """Helper function để hiển thị bảng video"""
    rows = []
    for i, v in enumerate(top_videos, 1):
        s = v.get("stats", {})
        m = v.get("metrics", {})
        rows.append(
            {
                "#": i,
                "Video ID": v.get("id", ""),
                "Mô tả": (v.get("description", "") or "")[:60] + "...",
                "Views": f"{s.get('play_count', 0):,}",
                "Likes": f"{s.get('like_count', 0):,}",
                "Comments": f"{s.get('comment_count', 0):,}",
                "Shares": f"{s.get('share_count', 0):,}",
                "Engagement %": round(m.get("engagement_rate", 0), 2),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                column_config={
                    "Engagement %": st.column_config.ProgressColumn(
                        "Engagement %", min_value=0, max_value=20, format="%.2f%%"
                    )
                })


# ============================================================================
# TRANG 2: SENTIMENT THEO VIDEO
# ============================================================================
def page_video_sentiment(videos, comments):
    st.title("Sentiment theo từng Video")
    st.caption("Luồng đề xuất: 1) Lọc dữ liệu  2) Đọc bảng tổng hợp  3) Xem biểu đồ  4) Đi sâu từng video")

    df_c = _prepare_comments_df(comments)
    if df_c.empty:
        st.warning("Không có dữ liệu comment.")
        return

    # --- Bảng tổng hợp per-video ---
    st.subheader("1) Bảng tổng hợp: Comment đã gán nhãn và coverage theo video")

    video_rows = []
    for v in videos:
        vid = str(v.get("id", ""))
        vc = df_c[df_c["video_id"].astype(str) == vid]
        total = len(vc)
        if total == 0:
            continue
        pos = int((vc["sentiment"] == "positive").sum())
        neu = int((vc["sentiment"] == "neutral").sum())
        neg = int((vc["sentiment"] == "negative").sum())
        unlabeled = int((vc["sentiment"] == "unlabeled").sum())
        labeled_total = pos + neu + neg
        stats = v.get("stats", {})
        plays = stats.get("play_count", 0)
        likes = stats.get("like_count", 0)
        shares = stats.get("share_count", 0)
        cmt = stats.get("comment_count", 0)
        full_desc = (v.get("description", "") or "").strip()
        desc_short = full_desc[:60] + ("…" if len(full_desc) > 60 else "")
        url = v.get("video_url", "")

        # Nhãn chiếm đa số
        dominant = (
            max(
                [("✅ Tích cực", pos), ("⚪ Trung tính", neu), ("❌ Tiêu cực", neg)],
                key=lambda x: x[1],
            )[0]
            if labeled_total
            else "⚫ Chưa gán nhãn"
        )

        video_rows.append(
            {
                "Video ID": vid,
                "🔗 Link": url,
                "Mô tả": desc_short,
                "Plays": plays,
                "❤️ Likes": likes,
                "↗️ Shares": shares,
                "💬 TikTok comments": cmt,
                "Tổng comment": total,
                "⚫ Chưa gán": unlabeled,
                "Tổng đã gán": labeled_total,
                "✅ Tích cực": pos,
                "⚪ Trung tính": neu,
                "❌ Tiêu cực": neg,
                "% Tích cực": round(pos / labeled_total * 100, 1) if labeled_total else 0,
                "% Trung tính": round(neu / labeled_total * 100, 1) if labeled_total else 0,
                "% Tiêu cực": round(neg / labeled_total * 100, 1) if labeled_total else 0,
                "Coverage %": round(labeled_total / total * 100, 1) if total else 0,
                "Thu thập/TikTok %": round(total / cmt * 100, 1) if cmt else 0,
                "Score": round((pos - neg) / labeled_total, 2) if labeled_total else 0,
                "Xu hướng": dominant,
            }
        )

    df_summary = pd.DataFrame(video_rows)
    if df_summary.empty:
        st.info("Không có video nào có comment để hiển thị.")
        return

    df_summary = df_summary.sort_values("Tổng comment", ascending=False)
    total_comments_in_table = int(df_summary["Tổng comment"].sum())

    # --- Bộ lọc tổng hợp ---
    st.markdown("#### Bộ lọc")
    max_comments = int(df_summary["Tổng comment"].max())
    default_state = {
        "tbl_min_comments": 1,
        "tbl_sort_by": "Tổng comment",
        "tbl_search": "",
        "tbl_dominant_filter": ["✅ Tích cực", "⚪ Trung tính", "❌ Tiêu cực"],
    }
    for k, v in default_state.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if st.session_state["tbl_min_comments"] > max_comments:
        st.session_state["tbl_min_comments"] = max_comments

    with st.container(border=True):
        col_f1, col_f2, col_f3 = st.columns([2, 2, 3])
        with col_f1:
            min_comments = st.slider(
                "Tối thiểu số comment",
                0,
                max_comments,
                key="tbl_min_comments",
            )
        with col_f2:
            sort_by = st.selectbox(
                "Sắp xếp theo",
                ["Tổng comment", "💬 TikTok comments", "% Tích cực", "% Tiêu cực", "% Trung tính", "Score", "Plays", "❤️ Likes"],
                key="tbl_sort_by",
            )
        with col_f3:
            search_desc = st.text_input(
                "🔍 Tìm theo mô tả video",
                placeholder="Nhập từ khóa…",
                key="tbl_search",
            )

        col_f4, col_f5 = st.columns([4, 1])
        with col_f4:
            dominant_filter = st.multiselect(
                "Lọc theo sentiment trội",
                ["✅ Tích cực", "⚪ Trung tính", "❌ Tiêu cực"],
                key="tbl_dominant_filter",
            )
        with col_f5:
            if st.button("Reset lọc", use_container_width=True):
                for k, v in default_state.items():
                    st.session_state[k] = v
                st.rerun()

    df_filtered = df_summary[df_summary["Tổng comment"] >= min_comments]
    if search_desc.strip():
        df_filtered = df_filtered[
            df_filtered["Mô tả"].str.contains(search_desc.strip(), case=False, na=False)
        ]
    if dominant_filter:
        df_filtered = df_filtered[df_filtered["Xu hướng"].isin(dominant_filter)]
    df_filtered = df_filtered.sort_values(sort_by, ascending=False)

    # Metrics tổng hợp
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🎬 Videos hiển thị", f"{len(df_filtered)}")
    collected_now = int(df_filtered['Tổng comment'].sum())
    tiktok_now = int(df_filtered['💬 TikTok comments'].sum())
    m2.metric("💬 Comment thu thập", f"{collected_now:,}", 
              help=f"Toàn bộ dữ liệu thu thập: {total_comments_in_table:,} comment từ {len(df_summary)} video")
    m3.metric("✅ Tích cực", f"{int(df_filtered['✅ Tích cực'].sum()):,}")
    m4.metric("💬 Comment TikTok", f"{tiktok_now:,}")

    st.markdown("#### 2) Bảng dữ liệu video")
    table_cols = [
        "🔗 Link", "Mô tả", "Plays", "❤️ Likes", "↗️ Shares", "💬 TikTok comments", "Tổng comment",
        "⚫ Chưa gán", "Tổng đã gán", "Coverage %",
        "Thu thập/TikTok %", "✅ Tích cực", "⚪ Trung tính", "❌ Tiêu cực", "% Tích cực", "% Trung tính", "% Tiêu cực", "Score", "Xu hướng"
    ]
    st.dataframe(
        df_filtered[table_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "🔗 Link": st.column_config.LinkColumn(
                "🔗 Xem video", display_text="▶ TikTok"
            ),
            "Mô tả": st.column_config.TextColumn("Mô tả video", width="large"),
            "Plays": st.column_config.NumberColumn("▶️ Plays", format="%d"),
            "❤️ Likes": st.column_config.NumberColumn("❤️ Likes", format="%d"),
            "↗️ Shares": st.column_config.NumberColumn("↗️ Shares", format="%d"),
            "💬 TikTok comments": st.column_config.NumberColumn("💬 TikTok comments", format="%d"),
            "Coverage %": st.column_config.ProgressColumn(
                "Coverage %", min_value=0, max_value=100, format="%.1f%%"
            ),
            "Thu thập/TikTok %": st.column_config.ProgressColumn(
                "Thu thập/TikTok %", min_value=0, max_value=100, format="%.1f%%"
            ),
            "% Tích cực": st.column_config.ProgressColumn(
                "% Tích cực", min_value=0, max_value=100, format="%.1f%%"
            ),
            "% Trung tính": st.column_config.ProgressColumn(
                "% Trung tính", min_value=0, max_value=100, format="%.1f%%"
            ),
            "% Tiêu cực": st.column_config.ProgressColumn(
                "% Tiêu cực", min_value=0, max_value=100, format="%.1f%%",
            ),
            "Score": st.column_config.NumberColumn("Score", format="%.2f"),
            "Xu hướng": st.column_config.TextColumn("Xu hướng"),
        },
    )

    st.caption(
        f"Đang hiển thị {collected_now:,}/{total_comments_in_table:,} comment thu thập theo bộ lọc hiện tại. "
        f"Tổng comment TikTok tương ứng: {tiktok_now:,}. "
        f"📊 Score = (Tích cực − Tiêu cực) / Tổng comment đã gán nhãn. "
        f"Score > 0 = thiên tích cực, < 0 = thiên tiêu cực."
    )

    # --- Biểu đồ stacked bar ---
    st.subheader("3) Biểu đồ Sentiment theo Video")

    total_comments_all = int(df_filtered["Tổng comment"].sum())
    n_videos_available = len(df_filtered)

    if n_videos_available == 0:
        st.info("Không có video nào khớp bộ lọc hiện tại.")
    else:
        col_chart1, col_chart2 = st.columns([3, 1])
        with col_chart1:
            min_show = 1 if n_videos_available < 5 else 5
            n_show = st.slider(
                "Số video hiển thị",
                min_value=min_show,
                max_value=n_videos_available,
                value=min(20, n_videos_available),
                step=1 if n_videos_available < 5 else 5,
                key="chart_n_videos",
            )
        with col_chart2:
            sort_chart = st.selectbox(
                "Sắp xếp biểu đồ",
                ["Tổng comment", "% Tiêu cực", "Score"],
                key="chart_sort",
            )

        topN = df_filtered.nlargest(n_show, sort_chart).copy()
        shown_comments = int(topN["Tổng comment"].sum())

        # Tạo nhãn hiển thị: mô tả ngắn + 6 số cuối ID
        topN["label"] = topN.apply(
            lambda r: (
                (r["Mô tả"][:28] + "…" if len(r["Mô tả"]) > 28 else r["Mô tả"])
                + f"\n[…{str(r['Video ID'])[-6:]}]"
            )
            if r["Mô tả"].strip()
            else f"[…{str(r['Video ID'])[-6:]}]",
            axis=1,
        )
        # Hover text chi tiết
        topN["hover"] = topN.apply(
            lambda r: (
                f"<b>{r['Mô tả'][:60] or 'Không có mô tả'}</b><br>"
                f"ID: {r['Video ID']}<br>"
                f"Tổng: {r['Tổng comment']} | ✅ {r['✅ Tích cực']} | ⚪ {r['⚪ Trung tính']} | ❌ {r['❌ Tiêu cực']}<br>"
                f"Score: {r['Score']}"
            ),
            axis=1,
        )

        fig_bar = go.Figure()
        fig_bar.add_trace(
            go.Bar(
                name="Tích cực",
                x=topN["label"],
                y=topN["✅ Tích cực"],
                marker_color="#2ecc71",
                hovertext=topN["hover"],
                hoverinfo="text",
            )
        )
        fig_bar.add_trace(
            go.Bar(
                name="Trung tính",
                x=topN["label"],
                y=topN["⚪ Trung tính"],
                marker_color="#3498db",
                hovertext=topN["hover"],
                hoverinfo="text",
            )
        )
        fig_bar.add_trace(
            go.Bar(
                name="Tiêu cực",
                x=topN["label"],
                y=topN["❌ Tiêu cực"],
                marker_color="#e74c3c",
                hovertext=topN["hover"],
                hoverinfo="text",
            )
        )
        chart_height = max(520, 350 + n_show * 8)
        fig_bar.update_layout(
            barmode="stack",
            xaxis_title="Video (mô tả + ID)",
            yaxis_title="Số lượng bình luận",
            height=chart_height,
            xaxis=dict(tickangle=-35, tickfont=dict(size=10)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(b=160),
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.caption(
            f"📊 Hiển thị **{n_show}/{n_videos_available}** video — "
            f"**{shown_comments:,}/{total_comments_all:,}** comment "
            f"({shown_comments/total_comments_all*100:.1f}% tổng dữ liệu). "
            f"Tăng slider để xem thêm."
        )

    # --- Chi tiết 1 video khi click ---
    st.subheader("4) 🔍 Xem chi tiết một Video")
    video_options = df_filtered["Video ID"].tolist()
    if video_options:
        desc_by_id = dict(zip(df_filtered["Video ID"], df_filtered["Mô tả"]))
        selected = st.selectbox(
            "Chọn video",
            video_options,
            format_func=lambda x: f"{str(x)[-6:]} | {desc_by_id.get(x, '')}",
        )
        vc = df_c[df_c["video_id"].astype(str) == str(selected)]

        st.write(f"**Tổng: {len(vc)} comments** — "
                 f"✅ {int((vc['sentiment']=='positive').sum())} | "
                 f"⚪ {int((vc['sentiment']=='neutral').sum())} | "
                 f"❌ {int((vc['sentiment']=='negative').sum())} | "
                 f"⚫ {int((vc['sentiment']=='unlabeled').sum())}")

        # Lọc theo sentiment
        filter_sent = st.multiselect(
            "Lọc sentiment",
            ["positive", "neutral", "negative", "unlabeled"],
            default=["positive", "neutral", "negative", "unlabeled"],
            key="video_detail_filter",
        )
        vc_filtered = vc[vc["sentiment"].isin(filter_sent)]

        display_cols = ["text", "sentiment", "confidence", "author", "likes"]
        available_cols = [c for c in display_cols if c in vc_filtered.columns]
        st.dataframe(
            vc_filtered[available_cols].sort_values("confidence"),
            use_container_width=True,
            hide_index=True,
            column_config={
                "text": st.column_config.TextColumn("Bình luận", width="large"),
                "sentiment": st.column_config.TextColumn("Nhãn"),
                "confidence": st.column_config.ProgressColumn(
                    "Độ tin cậy", min_value=0, max_value=1, format="%.2f"
                ),
            },
        )

    st.divider()

    # -----------------------------------------------------------------------
    # PHẦN 2: Comment được like nhiều nhất theo từng sentiment
    # -----------------------------------------------------------------------
    st.subheader("❤️ Comment được like nhiều nhất theo Sentiment")

    if "likes" in df_c.columns:
        df_likes = df_c.copy()
        df_likes["likes"] = pd.to_numeric(df_likes["likes"], errors="coerce").fillna(0).astype(int)

        top_n = st.slider("Top N comment mỗi nhóm", 3, 20, 5, key="top_likes_n")
        sent_colors = {"positive": "🟢", "neutral": "🔵", "negative": "🔴"}

        cols_like = st.columns(3)
        for i, sent in enumerate(["positive", "neutral", "negative"]):
            with cols_like[i]:
                st.markdown(f"**{sent_colors[sent]} {sent.capitalize()}**")
                top = (
                    df_likes[df_likes["sentiment"] == sent]
                    .nlargest(top_n, "likes")[["text", "author", "likes", "video_id"]]
                    .reset_index(drop=True)
                )
                if top.empty:
                    st.caption("Không có dữ liệu")
                else:
                    for _, row in top.iterrows():
                        with st.container(border=True):
                            st.markdown(f"❤️ **{row['likes']}** &nbsp; `{str(row.get('author',''))[:20]}`")
                            st.caption(row["text"][:120] + ("…" if len(row["text"]) > 120 else ""))
    else:
        st.caption("Dữ liệu không có cột `likes`.")

    st.divider()

    # -----------------------------------------------------------------------
    # PHẦN 3: Tác giả hay comment negative nhất
    # -----------------------------------------------------------------------
    st.subheader("👤 Tác giả hay comment tiêu cực nhất")

    if "author" in df_c.columns:
        df_auth = df_c.copy()
        df_auth["author"] = df_auth["author"].fillna("(ẩn danh)")

        n_top_authors = st.slider("Số tác giả hiển thị", 5, 30, 10, key="top_neg_authors")

        author_stats = (
            df_auth.groupby("author")["sentiment"]
            .value_counts()
            .unstack(fill_value=0)
        )
        for col in ["positive", "neutral", "negative"]:
            if col not in author_stats.columns:
                author_stats[col] = 0
        author_stats["total"] = author_stats[["positive", "neutral", "negative"]].sum(axis=1)
        author_stats["neg_rate"] = author_stats["negative"] / author_stats["total"]
        author_stats = author_stats[author_stats["total"] >= 2]  # bỏ tác giả chỉ 1 comment

        col_auth1, col_auth2 = st.columns(2)
        with col_auth1:
            sort_by_auth = st.radio(
                "Sắp xếp theo",
                ["Số comment tiêu cực", "Tỉ lệ tiêu cực (%)"],
                horizontal=True,
                key="auth_sort",
            )

        sort_col = "negative" if sort_by_auth == "Số comment tiêu cực" else "neg_rate"
        top_neg = author_stats.nlargest(n_top_authors, sort_col).reset_index()
        top_neg["neg_rate_pct"] = (top_neg["neg_rate"] * 100).round(1)

        df_auth_display = top_neg[["author", "total", "positive", "neutral", "negative", "neg_rate_pct"]].rename(
            columns={
                "author": "Tác giả",
                "total": "Tổng comment",
                "positive": "✅ Tích cực",
                "neutral": "⚪ Trung tính",
                "negative": "❌ Tiêu cực",
                "neg_rate_pct": "% Tiêu cực",
            }
        )
        st.dataframe(
            df_auth_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "% Tiêu cực": st.column_config.ProgressColumn(
                    "% Tiêu cực", min_value=0, max_value=100, format="%.1f%%"
                ),
            },
        )

        # Bar chart tác giả
        fig_auth = px.bar(
            top_neg,
            x="author",
            y=["positive", "neutral", "negative"],
            title=f"Top {n_top_authors} tác giả — phân bổ sentiment",
            labels={"value": "Số comment", "author": "Tác giả", "variable": "Sentiment"},
            color_discrete_map={"positive": "#2ecc71", "neutral": "#3498db", "negative": "#e74c3c"},
            barmode="stack",
            height=400,
        )
        fig_auth.update_xaxes(tickangle=-30)
        st.plotly_chart(fig_auth, use_container_width=True)

        # --- Xem chi tiết comment tiêu cực của một tác giả ---
        st.markdown("#### 🔎 Xem comment tiêu cực của tác giả")
        author_list = top_neg["author"].tolist()
        selected_author = st.selectbox(
            "Chọn tác giả",
            author_list,
            key="neg_author_select",
        )
        if selected_author:
            neg_comments = df_auth[
                (df_auth["author"] == selected_author)
                & (df_auth["sentiment"] == "negative")
            ]
            all_comments = df_auth[df_auth["author"] == selected_author]

            col_a1, col_a2, col_a3 = st.columns(3)
            col_a1.metric("Tổng comment", len(all_comments))
            col_a2.metric("❌ Tiêu cực", len(neg_comments))
            col_a3.metric(
                "% Tiêu cực",
                f"{len(neg_comments)/len(all_comments)*100:.1f}%" if len(all_comments) > 0 else "0%",
            )

            if neg_comments.empty:
                st.info("Tác giả này không có comment tiêu cực.")
            else:
                display_neg_cols = ["text", "confidence", "likes", "video_id"]
                available_neg_cols = [c for c in display_neg_cols if c in neg_comments.columns]
                st.dataframe(
                    neg_comments[available_neg_cols].reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "text": st.column_config.TextColumn("Nội dung comment", width="large"),
                        "confidence": st.column_config.ProgressColumn(
                            "Độ tin cậy", min_value=0, max_value=1, format="%.2f"
                        ),
                        "likes": st.column_config.NumberColumn("❤️ Likes"),
                        "video_id": st.column_config.TextColumn("Video ID"),
                    },
                )
    else:
        st.caption("Dữ liệu không có cột `author`.")

    st.divider()

    # -----------------------------------------------------------------------
    # PHẦN 4: Xu hướng sentiment theo thời gian
    # -----------------------------------------------------------------------
    st.subheader("📈 Xu hướng Sentiment theo thời gian")

    if "created_at" in df_c.columns:
        df_time = df_c.copy()
        df_time["created_at"] = pd.to_datetime(df_time["created_at"], errors="coerce")
        df_time = df_time.dropna(subset=["created_at"])

        if len(df_time) < 5:
            st.caption("Không đủ dữ liệu thời gian.")
        else:
            granularity = st.radio(
                "Đơn vị thời gian",
                ["Ngày", "Tuần", "Tháng"],
                horizontal=True,
                key="time_gran",
            )
            freq_map = {"Ngày": "D", "Tuần": "W", "Tháng": "ME"}
            freq = freq_map[granularity]

            df_time["period"] = df_time["created_at"].dt.to_period(freq).dt.to_timestamp()

            trend = (
                df_time.groupby(["period", "sentiment"])
                .size()
                .reset_index(name="count")
            )

            # Tính % cho mỗi kỳ
            totals = trend.groupby("period")["count"].transform("sum")
            trend["pct"] = (trend["count"] / totals * 100).round(1)

            col_tm1, col_tm2 = st.columns(2)
            with col_tm1:
                show_pct = st.checkbox("Hiển thị theo % (thay vì số lượng)", value=False, key="time_pct")

            y_col = "pct" if show_pct else "count"
            y_label = "Tỉ lệ (%)" if show_pct else "Số comment"

            fig_trend = px.line(
                trend,
                x="period",
                y=y_col,
                color="sentiment",
                markers=True,
                title=f"Xu hướng sentiment theo {granularity.lower()}",
                labels={"period": "Thời gian", y_col: y_label, "sentiment": "Sentiment"},
                color_discrete_map={"positive": "#2ecc71", "neutral": "#3498db", "negative": "#e74c3c"},
                height=450,
            )
            fig_trend.update_layout(hovermode="x unified")
            st.plotly_chart(fig_trend, use_container_width=True)

            # Bảng tổng hợp
            with st.expander("📋 Bảng dữ liệu theo thời gian"):
                pivot = trend.pivot_table(
                    index="period", columns="sentiment", values="count", fill_value=0
                ).reset_index()
                pivot.columns.name = None
                st.dataframe(pivot, use_container_width=True, hide_index=True)
    else:
        st.caption("Dữ liệu không có cột `created_at` — không thể vẽ xu hướng thời gian.")


# ============================================================================
# TRANG 3: CHI TIẾT BÌNH LUẬN
# ============================================================================
def page_comment_detail(videos, comments):
    st.title("Chi tiết bình luận")

    df_c = _prepare_comments_df(comments)
    if df_c.empty:
        st.warning("Không có dữ liệu comment.")
        return

    # --- Bộ lọc ---
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_sentiment = st.multiselect(
            "Sentiment",
            ["positive", "neutral", "negative", "unlabeled"],
            default=["positive", "neutral", "negative", "unlabeled"],
            key="detail_sentiment",
        )
    with col2:
        conf_range = st.slider(
            "Confidence", 0.0, 1.0, (0.0, 1.0), step=0.05, key="detail_conf"
        )
    with col3:
        video_ids = ["Tất cả"] + sorted(df_c["video_id"].astype(str).unique().tolist())
        selected_video = st.selectbox("Video", video_ids, key="detail_video")

    # Áp dụng lọc
    mask = df_c["sentiment"].isin(filter_sentiment)
    mask &= df_c["confidence"].between(conf_range[0], conf_range[1])
    if selected_video != "Tất cả":
        mask &= df_c["video_id"].astype(str) == selected_video

    filtered = df_c[mask]

    # --- Thống kê ---
    st.write(
        f"Hiển thị **{len(filtered)}** / {len(df_c)} bình luận | "
        f"✅ {int((filtered['sentiment']=='positive').sum())} "
        f"⚪ {int((filtered['sentiment']=='neutral').sum())} "
        f"❌ {int((filtered['sentiment']=='negative').sum())}"
    )

    # --- Bảng chi tiết ---
    display_cols = ["video_id", "text", "sentiment", "confidence", "author", "likes"]
    available_cols = [c for c in display_cols if c in filtered.columns]

    st.dataframe(
        filtered[available_cols].sort_values("confidence"),
        use_container_width=True,
        hide_index=True,
        height=600,
        column_config={
            "text": st.column_config.TextColumn("Bình luận", width="large"),
            "sentiment": "Nhãn",
            "confidence": st.column_config.ProgressColumn(
                "Độ tin cậy", min_value=0, max_value=1, format="%.3f"
            ),
            "video_id": st.column_config.TextColumn("Video ID", width="small"),
        },
    )


# ============================================================================
# TRANG 4: GÁN NHÃN THỦ CÔNG
# ============================================================================
def page_manual_labeling(videos, comments):
    st.title("Gán nhãn thủ công")
    st.info(
        "Trang này cho phép bạn review và sửa nhãn sentiment từng comment. "
        "Sau khi sửa, nhấn **Lưu** để cập nhật vào file gốc."
    )

    # Nút gán nhãn tự động bằng Gemini cho tất cả comment chưa thủ công
    st.divider()
    
    # Statistics box
    with st.expander("📊 Thống kê Gemini Analyzer", expanded=False):
        analyzer = get_gemini_analyzer_singleton()
        stats = analyzer.get_statistics()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Total Requests", stats["total_requests"])
        col1.metric("✅ Cache Hits", stats["cache_hits"])
        
        col2.metric("🌐 API Calls", stats["api_calls"])
        col2.metric("⚠️ Rate Limits", stats["rate_limits"])
        
        col3.metric("❌ Errors", stats["errors"])
        col3.metric("💾 Cache Size", stats["cache_size"])
        col3.metric("🎯 Cache Hit Rate", f"{stats['cache_hit_rate']:.1f}%")
        
        st.caption(f"Cache hit rate cao = tiết kiệm API quota. Model: {GEMINI_MODEL}")
    
    # Buttons
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("🤖 Gán nhãn tự động bằng Gemini", type="primary", use_container_width=True):
            with st.spinner("Đang phân tích bằng Gemini AI..."):
                updated = gemini_batch_label(comments, show_stats=True)
                if updated > 0:
                    st.success(f"✅ Đã gán nhãn {updated} comment bằng Gemini.")
                    st.cache_data.clear()
                    st.rerun()
    
    with col_btn2:
        analyzer = get_gemini_analyzer_singleton()
        if st.button("🗑️ Xóa cache", type="secondary", use_container_width=True):
            analyzer.clear_cache()
            st.success("✅ Đã xóa cache!")
            st.rerun()
    
    with col_btn3:
        if st.button("💾 Xuất cache", type="secondary", use_container_width=True):
            export_path = "data/export/gemini_cache_export.json"
            analyzer.export_cache(export_path)
            st.success(f"✅ Đã xuất cache → {export_path}")

    df_c = _prepare_comments_df(comments)
    if df_c.empty:
        st.warning("Không có dữ liệu.")
        return

    stat1, stat2, stat3, stat4 = st.columns(4)
    stat1.metric("Manual", int((df_c["method"] == "manual").sum()))
    stat2.metric("Gemini", int((df_c["method"] == "gemini").sum()))
    stat3.metric("Unlabeled", int((df_c["sentiment"] == "unlabeled").sum()))
    stat4.metric("Coverage", f"{len(_labeled_comments_df(df_c)) / len(df_c) * 100:.1f}%")

    # --- Bộ lọc ---
    col1, col2, col3 = st.columns(3)
    with col1:
        mode = st.radio(
            "Hiển thị",
            ["Tất cả comment", "Chỉ chưa gán nhãn", "Chỉ confidence thấp (< 0.7)", "Chỉ confidence thấp (< 0.5)"],
        )
    with col2:
        filter_sent = st.multiselect(
            "Lọc sentiment",
            ["positive", "neutral", "negative", "unlabeled"],
            default=["positive", "neutral", "negative", "unlabeled"],
            key="label_filter",
        )
    with col3:
        video_ids = ["Tất cả"] + sorted(df_c["video_id"].astype(str).unique().tolist())
        sel_video = st.selectbox("Video", video_ids, key="label_video")

    # Lọc
    mask = df_c["sentiment"].isin(filter_sent)
    if mode == "Chỉ chưa gán nhãn":
        mask &= df_c["sentiment"] == "unlabeled"
    elif mode == "Chỉ confidence thấp (< 0.7)":
        mask &= df_c["confidence"] < 0.7
    elif mode == "Chỉ confidence thấp (< 0.5)":
        mask &= df_c["confidence"] < 0.5
    if sel_video != "Tất cả":
        mask &= df_c["video_id"].astype(str) == sel_video

    subset = df_c[mask].reset_index(drop=True)
    st.write(f"**{len(subset)} bình luận** cần review")

    if subset.empty:
        return

    # Phân trang
    page_size = 20
    total_pages = max(1, (len(subset) - 1) // page_size + 1)
    page_num = st.number_input(
        f"Trang (1-{total_pages})", min_value=1, max_value=total_pages, value=1
    )
    start = (page_num - 1) * page_size
    end = min(start + page_size, len(subset))
    page_data = subset.iloc[start:end]

    st.divider()

    # --- Hiển thị từng comment với dropdown sửa nhãn ---
    changes = {}
    sentiment_options = ["unlabeled", "positive", "neutral", "negative"]
    color_map = {
        "positive": "🟢", "neutral": "🔵", "negative": "🔴", "unlabeled": "⚫"
    }

    for i, (idx, row) in enumerate(page_data.iterrows()):
        cols = st.columns([1, 5, 2, 2, 2, 2, 1])
        cols[0].write(f"**#{start + i + 1}**")
        raw_text = row.get("text", "")
        cleaned_for_labeling = basic_clean_text(raw_text) if _PREPROCESSOR_OK else raw_text
        cols[1].write(cleaned_for_labeling or raw_text)
        if cleaned_for_labeling and cleaned_for_labeling != raw_text:
            cols[1].caption(f"Gốc: {raw_text[:140]}{'…' if len(raw_text) > 140 else ''}")
        cols[2].write(
            f"{color_map.get(row['sentiment'], '')} {row['sentiment']}\n\n"
            f"Conf: {row['confidence']:.2f}"
        )

        current_sent = str(row.get("sentiment", "")).strip().lower()
        if current_sent not in sentiment_options:
            current_sent = "unlabeled"
        current_idx = sentiment_options.index(current_sent)
        new_label = cols[3].selectbox(
            "Nhãn mới",
            sentiment_options,
            index=current_idx,
            key=f"label_{start}_{i}",
        )

        # Checkbox xác nhận đúng
        confirm_key = f"confirm_{start}_{i}"
        confirmed = cols[4].checkbox("Xác nhận đúng", key=confirm_key)

        # Nút Gemini cho từng comment
        gemini_key = f"gemini_{start}_{i}"
        if cols[6].button("🤖", key=gemini_key, help="Phân tích bằng Gemini AI"):
            with st.spinner("Đang phân tích..."):
                sent, conf = gemini_analyze_single(row["text"])
                new_label = sent
                cols[5].success(f"Gemini: {sent} ({conf:.2f})")
                changes[idx] = {
                    "video_id": str(row.get("video_id", "")),
                    "text": row.get("text", ""),
                    "old": row["sentiment"],
                    "new": sent,
                    "confirm": True,
                }

        if new_label != row["sentiment"]:
            cols[5].success(f"→ {new_label}")
            changes[idx] = {
                "video_id": str(row.get("video_id", "")),
                "text": row.get("text", ""),
                "old": row["sentiment"],
                "new": new_label,
                "confirm": False,
            }
        elif confirmed:
            cols[5].success("Đã xác nhận đúng")
            changes[idx] = {
                "video_id": str(row.get("video_id", "")),
                "text": row.get("text", ""),
                "old": row["sentiment"],
                "new": row["sentiment"],
                "confirm": True,
            }
        else:
            cols[5].write("")


    # --- Nút lưu ---
    if changes:
        st.divider()
        st.warning(f"⚠️ Bạn đã thay đổi **{len(changes)}** nhãn trên trang này.")

        if st.button("💾 Lưu thay đổi vào file gốc", type="primary"):
            saved_count = _save_label_changes(changes, comments)
            if saved_count > 0:
                st.success(f"✅ Đã lưu {saved_count} cập nhật nhãn vào dữ liệu.")
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Không tìm thấy bản ghi phù hợp để cập nhật. Vui lòng thử lại hoặc đổi trang lọc.")


def _save_label_changes(changes: dict, comments_ref: list | None = None) -> int:
    """Lưu thay đổi nhãn vào tong_hop_comment.json và merged file"""
    try:
        # Chuẩn hóa thay đổi để so khớp ổn định
        normalized_changes = []
        for change in changes.values():
            normalized_changes.append(
                {
                    "video_id": str(change.get("video_id", "")),
                    "text": _norm_text(change.get("text", "")),
                    "old": _normalize_sentiment_value(change.get("old", "")),
                    "new": _normalize_sentiment_value(change.get("new", "")),
                    "confirm": bool(change.get("confirm", False)),
                }
            )

        def _apply_changes_to_comments(comments_list: list, track_count: bool = False) -> int:
            local_count = 0
            for comment in comments_list:
                c_vid = str(comment.get("video_id", ""))
                c_text = _norm_text(comment.get("text", ""))
                c_sent = _normalize_sentiment_value(comment.get("sentiment", ""))
                for change in normalized_changes:
                    new_sent = _normalize_sentiment_value(change["new"])
                    if new_sent not in ("positive", "neutral", "negative"):
                        continue
                    if c_vid != change["video_id"]:
                        continue
                    if c_text != change["text"]:
                        continue
                    if not change["confirm"] and c_sent != change["old"]:
                        continue
                    comment["sentiment"] = new_sent
                    comment["confidence"] = 1.0  # Nhãn thủ công = tin cậy 100%
                    comment["method"] = "manual"
                    if track_count:
                        local_count += 1
                    break
            return local_count

        # --- Cập nhật tong_hop_comment.json ---
        comment_data = load_comment_source()
        updated_count = 0

        for video in comment_data.get("videos", []):
            updated_count += _apply_changes_to_comments(video.get("comments", []), track_count=True)

        save_comment_source(comment_data)

        # --- Cập nhật merged file ---
        with open(MERGED_FILE, "r", encoding="utf-8") as f:
            merged = json.load(f)

        _apply_changes_to_comments(merged.get("comments", []))

        # Cập nhật comments trong videos
        for video in merged.get("videos", []):
            _apply_changes_to_comments(video.get("comments", []))

        with open(MERGED_FILE, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

        # Cập nhật dữ liệu trong bộ nhớ hiện tại để UI thấy ngay (trước khi rerun)
        if comments_ref is not None:
            _apply_changes_to_comments(comments_ref)

        return updated_count
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return 0


# ============================================================================
# TRANG 5: XUẤT / NHẬP EXCEL
# ============================================================================
def page_export_import(videos, comments):
    st.title("Xuất / Nhập Excel")

    df_c = _prepare_comments_df(comments)

    tab_export, tab_import = st.tabs(["📤 Xuất Excel", "📥 Nhập nhãn từ Excel"])

    # --- TAB XUẤT ---
    with tab_export:
        st.subheader("Xuất bình luận ra Excel để gán nhãn")

        export_mode = st.radio(
            "Chọn dữ liệu xuất",
            [
                f"Tất cả {len(df_c)} comment",
                f"Chỉ confidence < 0.7 ({int((df_c['confidence'] < 0.7).sum())} comment)",
                f"Chỉ confidence < 0.5 ({int((df_c['confidence'] < 0.5).sum())} comment)",
            ],
        )

        if st.button("📤 Tạo file Excel", type="primary"):
            if "< 0.7" in export_mode:
                export_df = df_c[df_c["confidence"] < 0.7].copy()
            elif "< 0.5" in export_mode:
                export_df = df_c[df_c["confidence"] < 0.5].copy()
            else:
                export_df = df_c.copy()

            # Chuẩn bị cột
            cols = ["video_id", "text", "sentiment", "confidence", "author", "likes"]
            available = [c for c in cols if c in export_df.columns]
            export_df = export_df[available].copy()
            if _PREPROCESSOR_OK and "text" in export_df.columns:
                export_df.insert(2, "text_cleaned", export_df["text"].astype(str).apply(basic_clean_text))
            export_df.rename(
                columns={
                    "sentiment": "phobert_sentiment",
                    "confidence": "phobert_confidence",
                },
                inplace=True,
            )
            export_df.insert(
                export_df.columns.get_loc("phobert_sentiment") + 1,
                "manual_sentiment",
                "",
            )
            export_df.insert(0, "stt", range(1, len(export_df) + 1))

            # Lưu file
            filename = f"comments_for_labeling_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = EXPORT_DIR / filename

            export_df.to_excel(filepath, index=False, engine="openpyxl")

            st.success(f"✅ Đã xuất {len(export_df)} comment → {filepath}")

            # Download button
            buffer = io.BytesIO()
            export_df.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)

            st.download_button(
                label="⬇️ Tải file Excel",
                data=buffer,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            st.info(
                "**Hướng dẫn:**\n"
                "1. Mở file Excel\n"
                "2. Điền cột `manual_sentiment` bằng: **positive**, **neutral**, hoặc **negative**\n"
                "3. Bỏ trống nếu đồng ý với nhãn PhoBERT\n"
                "4. Quay lại tab **Nhập nhãn từ Excel** để import"
            )

    # --- TAB NHẬP ---
    with tab_import:
        st.subheader("Nhập nhãn thủ công từ Excel")

        uploaded = st.file_uploader(
            "Chọn file Excel đã gán nhãn", type=["xlsx", "xlsm", "csv"]
        )

        if uploaded is not None:
            try:
                uploaded_name = str(getattr(uploaded, "name", "")).lower()
                if uploaded_name.endswith(".csv"):
                    df_import = pd.read_csv(uploaded)
                else:
                    df_import = pd.read_excel(uploaded, engine="openpyxl")
            except Exception as e:
                st.error(f"Khong doc duoc file upload: {e}")
                return

            st.write(f"Đã tải: **{len(df_import)} dòng**")

            # Kiểm tra cột manual_sentiment
            if "manual_sentiment" not in df_import.columns:
                st.error("❌ File thiếu cột `manual_sentiment`!")
                return

            manual_series = df_import["manual_sentiment"].fillna("").astype(str).str.strip()

            # Đếm nhãn đã gán
            labeled = df_import[manual_series != ""].copy()
            labeled["manual_sentiment"] = manual_series[manual_series != ""]

            valid_labels = labeled[
                labeled["manual_sentiment"].str.lower().isin(
                    ["positive", "neutral", "negative"]
                )
            ]

            invalid = labeled[~labeled.index.isin(valid_labels.index)]

            st.write(
                f"✅ **{len(valid_labels)}** comment đã gán nhãn hợp lệ | "
                f"⚠️ **{len(invalid)}** nhãn không hợp lệ | "
                f"⬜ **{len(df_import) - len(labeled)}** bỏ trống (giữ nhãn PhoBERT)"
            )

            if len(invalid) > 0:
                st.warning("Nhãn không hợp lệ (phải là positive/neutral/negative):")
                st.dataframe(invalid[["stt", "text", "manual_sentiment"]].head(10))

            if len(valid_labels) > 0:
                # Preview
                st.write("**Preview thay đổi:**")
                preview = valid_labels[
                    ["stt", "video_id", "text", "phobert_sentiment", "manual_sentiment"]
                ].head(20)
                st.dataframe(preview, use_container_width=True, hide_index=True)

                if st.button("💾 Áp dụng nhãn vào dữ liệu", type="primary"):
                    count = _apply_excel_labels(valid_labels)
                    if count > 0:
                        st.success(f"✅ Đã cập nhật {count} nhãn!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.warning("Không có bản ghi nào được cập nhật từ file Excel.")


def _apply_excel_labels(labeled_df: pd.DataFrame) -> int:
    """Áp dụng nhãn từ Excel vào cả tong_hop_comment.json và merged file"""
    count = 0

    # Tạo lookup: (video_id, text) → new_sentiment
    label_map = {}
    for _, row in labeled_df.iterrows():
        vid = str(row.get("video_id", ""))
        text = _norm_text(row.get("text", ""))
        new_sent = str(row["manual_sentiment"]).strip().lower()
        if new_sent in ("positive", "neutral", "negative"):
            label_map[(vid, text)] = new_sent

    # --- Cập nhật tong_hop_comment.json ---
    comment_data = load_comment_source()
    for video in comment_data.get("videos", []):
        vid = str(video.get("video_id", ""))
        for comment in video.get("comments", []):
            key = (vid, _norm_text(comment.get("text", "")))
            if key in label_map:
                comment["sentiment"] = label_map[key]
                comment["confidence"] = 1.0
                comment["method"] = "manual"
                count += 1
    save_comment_source(comment_data)

    # --- Cập nhật merged file ---
    if MERGED_FILE.exists():
        with open(MERGED_FILE, "r", encoding="utf-8") as f:
            merged = json.load(f)

        for comment in merged.get("comments", []):
            key = (str(comment.get("video_id", "")), _norm_text(comment.get("text", "")))
            if key in label_map:
                comment["sentiment"] = label_map[key]
                comment["confidence"] = 1.0
                comment["method"] = "manual"

        for video in merged.get("videos", []):
            for comment in video.get("comments", []):
                key = (str(comment.get("video_id", "")), _norm_text(comment.get("text", "")))
                if key in label_map:
                    comment["sentiment"] = label_map[key]
                    comment["confidence"] = 1.0
                    comment["method"] = "manual"

        with open(MERGED_FILE, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

    return count


# ============================================================================
# TRANG 6: PHÂN TÍCH CHỦ ĐỀ & TRANH CÃI
# ============================================================================

# Bảng từ khóa phân loại chủ đề — có thể mở rộng tự do
_TOPIC_KEYWORDS = {
    "📚 Tuyển sinh": [
        "tuyển sinh", "nhập học", "xét tuyển", "đăng ký", "nv1", "ưu tiên",
        "điểm chuẩn", "hồ sơ", "học sinh", "thí sinh",
    ],
    "💰 Học phí & Học bổng": [
        "học phí", "học bổng", "miễn giảm", "hỗ trợ", "học bổng khuyến khích",
        "học bổng tài năng", "tài chính", "tiền", "chi phí",
    ],
    "🎓 Việc làm & Tốt nghiệp": [
        "thực tập", "tốt nghiệp", "ra trường", "việc làm", "doanh nghiệp",
        "công ty", "tuyển dụng", "intern", "sinh viên tốt nghiệp",
    ],
    "🏠 Ký túc xá": [
        "ký túc xá", "ktx", "ở trọ", "phòng trọ", "chỗ ở", "nội trú",
    ],
    "🎉 Sự kiện & Lễ hội": [
        "sự kiện", "lễ hội", "hội trại", "khai giảng", "bế giảng",
        "lễ tốt nghiệp", "festival", "ngày hội", "kỷ niệm",
    ],
    "🔥 Viral & Trending": [
        "viral", "hot", "trend", "ontop", "nổi tiếng", "triệu view",
        "fyp", "foryou", "foryoupage",
    ],
    "🏃 Hoạt động Sinh viên": [
        "thể thao", "văn nghệ", "clb", "câu lạc bộ", "tình nguyện",
        "hội sinh viên", "đoàn trường", "cuộc thi",
    ],
    "🔬 Nghiên cứu & Khoa học": [
        "nghiên cứu", "khoa học", "đề tài", "hội nghị", "công trình",
        "sáng tạo", "startup", "khởi nghiệp",
    ],
    "🏫 Cơ sở vật chất": [
        "cơ sở vật chất", "thư viện", "phòng học", "lab", "phòng thí nghiệm",
        "căng tin", "sân", "cơ sở",
    ],
}


def _classify_topic(description: str, hashtags: list) -> str:
    """Phân loại chủ đề cho 1 video dựa trên description và hashtags."""
    text = (description or "").lower() + " " + " ".join(hashtags or []).lower()
    for topic, keywords in _TOPIC_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return topic
    return "📌 Khác"


def page_topic_analysis(videos: list, comments: list):
    st.title("Phân tích Chủ đề & Video Xu hướng")
    st.caption(
        "Phân loại video theo nội dung caption → so sánh sentiment từng nhóm chủ đề. "
        "Tìm video có tín hiệu lên xu hướng (viral) dựa trên tương tác thực tế."
    )

    if not videos:
        st.warning("Không có dữ liệu video.")
        return

    # ---- Xây dựng DataFrame video với topic + sentiment từ comments ----
    df_c = _prepare_comments_df(comments)
    rows = []
    for v in videos:
        vid = str(v.get("id", ""))
        desc = v.get("description", "") or ""
        hashtags = v.get("hashtags", []) or []
        stats = v.get("stats", {}) or {}

        play  = int(stats.get("play_count", 0))
        like  = int(stats.get("like_count", 0))
        cmt   = int(stats.get("comment_count", 0))
        share = int(stats.get("share_count", 0))
        er    = (v.get("metrics", {}) or {}).get("engagement_rate", 0) or 0

        # Sentiment từ comments đã gán nhãn
        vc = df_c[df_c["video_id"].astype(str) == vid] if not df_c.empty else pd.DataFrame()
        pos = int((vc["sentiment"] == "positive").sum()) if not vc.empty else 0
        neu = int((vc["sentiment"] == "neutral").sum())  if not vc.empty else 0
        neg = int((vc["sentiment"] == "negative").sum()) if not vc.empty else 0
        total_labeled = pos + neu + neg

        topic = _classify_topic(desc, hashtags)
        share_rate  = round(share / play * 100, 3) if play > 0 else 0

        rows.append({
            "video_id":      vid,
            "Chủ đề":        topic,
            "Mô tả":         desc[:80] + ("…" if len(desc) > 80 else ""),
            "Caption gốc":   desc,
            "Thời điểm đăng": v.get("create_time", ""),
            "Số hashtag":    len(hashtags),
            "Độ dài caption": len(desc),
            "Hashtags":      ", ".join(f"#{h}" for h in hashtags[:5]),
            "▶ Views":       play,
            "❤ Likes":       like,
            "💬 Comments":    cmt,
            "🔁 Shares":      share,
            "📈 ER%":         round(float(er), 2),
            "Share Rate%":   share_rate,
            "✅ Positive":    pos,
            "⚪ Neutral":     neu,
            "❌ Negative":    neg,
            "Tổng nhãn":     total_labeled,
            "% Positive":    round(pos / total_labeled * 100, 1) if total_labeled else 0,
            "% Negative":    round(neg / total_labeled * 100, 1) if total_labeled else 0,
        })

    df = pd.DataFrame(rows)

    tab1, tab2 = st.tabs(["A · Phân loại Chủ đề", "B · Video Xu hướng (Viral)"])

    # =========================================================================
    # TAB A — PHÂN LOẠI CHỦ ĐỀ
    # =========================================================================
    with tab1:
        st.subheader("Phân bổ video theo chủ đề")
        topic_counts = df["Chủ đề"].value_counts().reset_index()
        topic_counts.columns = ["Chủ đề", "Số video"]

        col_pie, col_bar = st.columns(2)
        with col_pie:
            fig_pie = px.pie(
                topic_counts, names="Chủ đề", values="Số video",
                title="Tỉ lệ chủ đề",
                height=380,
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_bar:
            # Trung bình views theo chủ đề
            topic_views = (
                df.groupby("Chủ đề")[["▶ Views", "❤ Likes", "📈 ER%"]]
                .mean().round(0).reset_index()
                .sort_values("▶ Views", ascending=True)
            )
            fig_views = px.bar(
                topic_views, x="▶ Views", y="Chủ đề",
                orientation="h",
                title="Trung bình Views theo chủ đề",
                height=380,
                color="▶ Views",
                color_continuous_scale="Blues",
            )
            fig_views.update_layout(showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig_views, use_container_width=True)

        # Sentiment trung bình theo chủ đề (chỉ video có nhãn)
        st.subheader("Sentiment trung bình theo từng chủ đề")
        df_labeled = df[df["Tổng nhãn"] > 0].copy()

        if df_labeled.empty:
            st.caption("Chưa có video nào có nhãn sentiment.")
        else:
            topic_sent = (
                df_labeled.groupby("Chủ đề")[["% Positive", "% Negative"]]
                .mean().round(1).reset_index()
                .sort_values("% Positive", ascending=False)
            )
            topic_sent_melt = topic_sent.melt(
                id_vars="Chủ đề",
                value_vars=["% Positive", "% Negative"],
                var_name="Loại", value_name="%",
            )
            fig_sent = px.bar(
                topic_sent_melt, x="Chủ đề", y="%", color="Loại", barmode="group",
                color_discrete_map={"% Positive": "#2ecc71", "% Negative": "#e74c3c"},
                title="% Positive / Negative theo chủ đề",
                height=400,
            )
            fig_sent.update_xaxes(tickangle=-20)
            st.plotly_chart(fig_sent, use_container_width=True)

        # Bảng chi tiết theo chủ đề đã chọn
        st.subheader("📋 Xem video theo chủ đề")
        topic_options = sorted(df["Chủ đề"].unique())
        selected_topic = st.selectbox("Chọn chủ đề", ["-- Tất cả --"] + topic_options)
        df_show = df if selected_topic == "-- Tất cả --" else df[df["Chủ đề"] == selected_topic]

        st.dataframe(
            df_show[["Chủ đề", "Mô tả", "Hashtags", "▶ Views", "❤ Likes",
                      "💬 Comments", "🔁 Shares", "📈 ER%",
                      "✅ Positive", "⚪ Neutral", "❌ Negative"]]
                .sort_values("▶ Views", ascending=False),
            use_container_width=True, hide_index=True,
            column_config={
                "Mô tả": st.column_config.TextColumn("Mô tả", width="large"),
                "📈 ER%": st.column_config.NumberColumn(format="%.2f%%"),
            }
        )

    # =========================================================================
    # TAB B — VIRAL INSIGHTS
    # =========================================================================
    with tab2:
        st.subheader("Video Viral: Thực tế và Dự đoán")

        df_viral = df.copy()
        if df_viral.empty:
            st.warning("Không có dữ liệu video để phân tích viral.")
        else:
            for c in ["▶ Views", "❤ Likes", "🔁 Shares", "💬 Comments", "📈 ER%", "Số hashtag", "Độ dài caption"]:
                df_viral[c] = pd.to_numeric(df_viral[c], errors="coerce").fillna(0)

            views_safe = df_viral["▶ Views"].replace(0, 1)
            df_viral["Like/View%"] = (df_viral["❤ Likes"] / views_safe * 100).fillna(0)
            df_viral["Share/View%"] = (df_viral["🔁 Shares"] / views_safe * 100).fillna(0)
            df_viral["Comment/View%"] = (df_viral["💬 Comments"] / views_safe * 100).fillna(0)

            # -------------------------------------------------------------
            # PHẦN 1: VIDEO ĐÃ VIRAL (dựa trên tín hiệu trực tiếp + gián tiếp)
            # -------------------------------------------------------------
            st.markdown("### 1) Video đã viral theo tín hiệu thực tế")
            st.caption(
                "Tín hiệu trực tiếp: Views, Likes/View, Shares, Comments. "
                "Tín hiệu gián tiếp: ER%, Share/View%, Comment/View%."
            )

            q90_views = df_viral["▶ Views"].quantile(0.90)
            q75_lvr = df_viral["Like/View%"].quantile(0.75)
            q75_shares = df_viral["🔁 Shares"].quantile(0.75)
            q75_comments = df_viral["💬 Comments"].quantile(0.75)
            q90_share_rate = df_viral["Share/View%"].quantile(0.90)
            q90_comment_rate = df_viral["Comment/View%"].quantile(0.90)

            df_viral["f_views_top"] = df_viral["▶ Views"] >= q90_views
            df_viral["f_like_rate_high"] = df_viral["Like/View%"] >= q75_lvr
            df_viral["f_shares_high"] = df_viral["🔁 Shares"] >= q75_shares
            df_viral["f_comments_high"] = df_viral["💬 Comments"] >= q75_comments
            df_viral["f_er_good"] = df_viral["📈 ER%"] >= 5
            df_viral["f_er_viral"] = df_viral["📈 ER%"] >= 10
            df_viral["f_share_rate_abnormal"] = df_viral["Share/View%"] >= q90_share_rate
            df_viral["f_comment_rate_high"] = df_viral["Comment/View%"] >= q90_comment_rate

            # Shares được ưu tiên cao nhất trong điểm thực tế.
            s_views = df_viral["▶ Views"].rank(pct=True)
            s_like_rate = df_viral["Like/View%"].rank(pct=True)
            s_shares = df_viral["🔁 Shares"].rank(pct=True)
            s_comments = df_viral["💬 Comments"].rank(pct=True)
            s_er = df_viral["📈 ER%"].rank(pct=True)
            s_share_rate = df_viral["Share/View%"].rank(pct=True)
            s_comment_rate = df_viral["Comment/View%"].rank(pct=True)

            df_viral["Điểm viral thực tế"] = (
                100 * (
                    0.20 * s_views +
                    0.10 * s_like_rate +
                    0.25 * s_shares +
                    0.10 * s_comments +
                    0.10 * s_er +
                    0.20 * s_share_rate +
                    0.05 * s_comment_rate
                )
            ).round(1)

            df_viral["Đã viral"] = (
                df_viral["f_er_viral"] |
                ((df_viral["f_share_rate_abnormal"] | df_viral["f_shares_high"]) & df_viral["f_er_good"]) |
                (df_viral["f_views_top"] & (df_viral["f_shares_high"] | df_viral["f_comments_high"]))
            )

            def _reason_observed(row):
                reasons = []
                if row["f_views_top"]:
                    reasons.append("Views thuộc nhóm cao nhất")
                if row["f_like_rate_high"]:
                    reasons.append("Tỉ lệ like/view cao")
                if row["f_shares_high"]:
                    reasons.append("Shares cao")
                if row["f_comments_high"]:
                    reasons.append("Comments cao")
                if row["f_er_viral"]:
                    reasons.append("ER > 10%")
                elif row["f_er_good"]:
                    reasons.append("ER > 5%")
                if row["f_share_rate_abnormal"]:
                    reasons.append("Share/View cao bất thường")
                if row["f_comment_rate_high"]:
                    reasons.append("Comment/View cao")
                return ", ".join(reasons[:5]) if reasons else "Chưa đủ tín hiệu mạnh"

            df_viral["Lý do đã viral"] = df_viral.apply(_reason_observed, axis=1)
            observed = df_viral[df_viral["Đã viral"]].copy()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tổng video", len(df_viral))
            c2.metric("Video đã viral", len(observed))
            c3.metric("ER > 10%", int((df_viral["📈 ER%"] > 10).sum()))
            c4.metric("Share/View cao bất thường", int(df_viral["f_share_rate_abnormal"].sum()))

            if observed.empty:
                st.info("Chưa có video nào đạt điều kiện 'đã viral' theo tín hiệu thực tế.")
            else:
                top_obs_n = st.slider("Top N video đã viral", 5, 30, 10, key="observed_viral_n")
                observed_top = observed.sort_values(
                    ["Điểm viral thực tế", "▶ Views", "🔁 Shares"],
                    ascending=[False, False, False]
                ).head(top_obs_n)

                st.dataframe(
                    observed_top[[
                        "Chủ đề", "Mô tả", "▶ Views", "❤ Likes", "🔁 Shares", "💬 Comments", "📈 ER%",
                        "Like/View%", "Share/View%", "Comment/View%", "Điểm viral thực tế", "Lý do đã viral"
                    ]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Mô tả": st.column_config.TextColumn("Mô tả", width="large"),
                        "Lý do đã viral": st.column_config.TextColumn("Dựa vào đâu", width="large"),
                        "📈 ER%": st.column_config.NumberColumn("ER%", format="%.2f%%"),
                        "Like/View%": st.column_config.NumberColumn("Like/View%", format="%.3f%%"),
                        "Share/View%": st.column_config.NumberColumn("Share/View%", format="%.3f%%"),
                        "Comment/View%": st.column_config.NumberColumn("Comment/View%", format="%.3f%%"),
                        "Điểm viral thực tế": st.column_config.ProgressColumn(
                            "Điểm viral thực tế", min_value=0, max_value=100, format="%.1f"
                        ),
                    }
                )

            st.divider()

            # -------------------------------------------------------------
            # PHẦN 2: DỰ ĐOÁN VIDEO CÓ THỂ VIRAL
            # -------------------------------------------------------------
            st.markdown("### 2) Dự đoán video có thể viral")
            st.caption(
                "Input: thời điểm đăng, số hashtag, độ dài caption, sentiment caption (PhoBERT), "
                "lịch sử avg views kênh. Output: mức views dự đoán tương đối (cao/trung bình/thấp). "
                "Thời điểm đăng được xử lý chi tiết theo múi giờ VN: thứ, giờ, phút và slot 30 phút."
            )

            channel_avg_views = float(df_viral["▶ Views"].mean()) if len(df_viral) else 0.0
            df_viral["Thời điểm đăng"] = pd.to_datetime(df_viral["Thời điểm đăng"], errors="coerce", utc=True)
            df_viral["Thời điểm đăng (VN)"] = df_viral["Thời điểm đăng"].dt.tz_convert("Asia/Ho_Chi_Minh")
            df_viral["Thứ đăng"] = df_viral["Thời điểm đăng (VN)"].dt.weekday
            df_viral["Giờ đăng"] = df_viral["Thời điểm đăng (VN)"].dt.hour
            df_viral["Phút đăng"] = df_viral["Thời điểm đăng (VN)"].dt.minute
            df_viral["Slot 30p"] = (df_viral["Giờ đăng"] * 2 + (df_viral["Phút đăng"] >= 30).astype(float)).astype("Int64")
            df_viral["Nhãn giờ"] = df_viral["Giờ đăng"].apply(lambda h: f"{int(h):02d}:00" if pd.notna(h) else "N/A")

            def _time_bucket(hour_val):
                if pd.isna(hour_val):
                    return "N/A"
                h = int(hour_val)
                if 0 <= h < 6:
                    return "Đêm (00-05h)"
                if 6 <= h < 11:
                    return "Sáng (06-10h)"
                if 11 <= h < 14:
                    return "Trưa (11-13h)"
                if 14 <= h < 18:
                    return "Chiều (14-17h)"
                if 18 <= h < 22:
                    return "Tối (18-21h)"
                return "Khuya (22-23h)"

            df_viral["Khung giờ"] = df_viral["Giờ đăng"].apply(_time_bucket)
            dow_map = {
                0: "Thứ 2", 1: "Thứ 3", 2: "Thứ 4", 3: "Thứ 5",
                4: "Thứ 6", 5: "Thứ 7", 6: "Chủ nhật"
            }
            df_viral["Ngày đăng"] = df_viral["Thứ đăng"].map(dow_map).fillna("N/A")

            st.markdown("#### Biểu đồ thời điểm đăng hiệu quả")
            h_col, d_col = st.columns(2)

            with h_col:
                hour_perf = (
                    df_viral.dropna(subset=["Giờ đăng"]).groupby("Giờ đăng")["▶ Views"]
                    .mean().reindex(range(24), fill_value=0).reset_index()
                )
                hour_perf.columns = ["Giờ", "Views TB"]
                hour_perf["Gợi ý"] = hour_perf["Giờ"].apply(
                    lambda h: "Peak đề xuất" if (11 <= h <= 12) or (17 <= h <= 19) or (21 <= h <= 23) else "Khác"
                )
                fig_hour = px.bar(
                    hour_perf,
                    x="Giờ",
                    y="Views TB",
                    color="Gợi ý",
                    title="Hiệu suất theo giờ đăng (múi giờ VN)",
                    color_discrete_map={"Peak đề xuất": "#d62728", "Khác": "#7f8c8d"},
                    labels={"Giờ": "Giờ trong ngày", "Views TB": "Views trung bình"},
                    height=360,
                )
                fig_hour.add_vrect(x0=11 - 0.5, x1=12 + 0.5, fillcolor="#f39c12", opacity=0.12, line_width=0)
                fig_hour.add_vrect(x0=17 - 0.5, x1=19 + 0.5, fillcolor="#2ecc71", opacity=0.12, line_width=0)
                fig_hour.add_vrect(x0=21 - 0.5, x1=23 + 0.5, fillcolor="#3498db", opacity=0.12, line_width=0)
                st.plotly_chart(fig_hour, use_container_width=True)
                st.caption("Peak hours gợi ý: 11-12h, 17-19h, 21-23h.")

            with d_col:
                day_perf = (
                    df_viral.dropna(subset=["Thứ đăng"]).groupby("Thứ đăng")["▶ Views"]
                    .mean().reindex(range(7), fill_value=0).reset_index()
                )
                day_perf["Ngày"] = day_perf["Thứ đăng"].map(dow_map)
                day_perf["Gợi ý"] = day_perf["Thứ đăng"].apply(
                    lambda d: "Ngày tốt đề xuất" if d in [0, 1, 2, 4] else "Khác"
                )
                fig_day = px.bar(
                    day_perf,
                    x="Ngày",
                    y="▶ Views",
                    color="Gợi ý",
                    title="Hiệu suất theo ngày đăng",
                    color_discrete_map={"Ngày tốt đề xuất": "#e67e22", "Khác": "#95a5a6"},
                    labels={"▶ Views": "Views trung bình"},
                    height=360,
                )
                st.plotly_chart(fig_day, use_container_width=True)
                st.caption("Ngày tốt gợi ý: Thứ 2-4 và Thứ 6.")

            slot_stats = (
                df_viral.dropna(subset=["Thứ đăng", "Giờ đăng", "Slot 30p"]) 
                .groupby(["Thứ đăng", "Giờ đăng", "Slot 30p"])["▶ Views"]
                .agg(["mean", "count"])
                .to_dict("index")
            )
            hour_stats = (
                df_viral.dropna(subset=["Giờ đăng"]).groupby("Giờ đăng")["▶ Views"]
                .agg(["mean", "count"]).to_dict("index")
            )
            weekday_stats = (
                df_viral.dropna(subset=["Thứ đăng"]).groupby("Thứ đăng")["▶ Views"]
                .agg(["mean", "count"]).to_dict("index")
            )

            def _time_score(row):
                if pd.isna(row["Giờ đăng"]) or pd.isna(row["Thứ đăng"]) or pd.isna(row["Slot 30p"]):
                    return 0.5

                day = int(row["Thứ đăng"])
                hour = int(row["Giờ đăng"])
                slot = int(row["Slot 30p"])

                if (day, hour, slot) in slot_stats and slot_stats[(day, hour, slot)]["count"] >= 2:
                    base_views = float(slot_stats[(day, hour, slot)]["mean"])
                    fallback_weight = 1.0
                elif hour in hour_stats:
                    base_views = float(hour_stats[hour]["mean"])
                    fallback_weight = 0.75
                elif day in weekday_stats:
                    base_views = float(weekday_stats[day]["mean"])
                    fallback_weight = 0.6
                else:
                    base_views = channel_avg_views
                    fallback_weight = 0.5

                ratio = base_views / max(channel_avg_views, 1.0)
                ratio = min(max(ratio, 0.55), 1.45)
                score_core = (ratio - 0.55) / 0.9
                # Khi phải fallback mạnh, kéo score về trung tính để giảm overfit.
                return fallback_weight * score_core + (1 - fallback_weight) * 0.5

            def _hashtag_score(n_tag):
                # Kinh nghiệm nền tảng ngắn: cụm 2-6 hashtag thường ổn định hơn cực ít/cực nhiều.
                return max(0.0, 1.0 - min(abs(float(n_tag) - 4.0), 6.0) / 6.0)

            def _caption_len_score(length_val):
                # Caption quá ngắn hoặc quá dài thường giảm hiệu quả; vùng tối ưu quanh 90 ký tự.
                return max(0.0, 1.0 - min(abs(float(length_val) - 90.0), 120.0) / 120.0)

            df_viral["time_score"] = df_viral.apply(_time_score, axis=1)
            df_viral["hashtag_score"] = df_viral["Số hashtag"].apply(_hashtag_score)
            df_viral["caption_len_score"] = df_viral["Độ dài caption"].apply(_caption_len_score)

            caption_texts = tuple(df_viral["Caption gốc"].fillna("").astype(str).tolist())

            phobert_available = _PHOBERT_IMPORTABLE and is_model_available()
            caption_sent = []
            caption_conf = []

            if phobert_available and caption_texts:
                @st.cache_resource(show_spinner=False)
                def _load_phobert_for_viral_predictor():
                    return PhoBERTSentiment()

                @st.cache_data(show_spinner=False)
                def _predict_caption_sentiments(_captions: tuple[str, ...]):
                    mdl = _load_phobert_for_viral_predictor()
                    res = mdl.predict_batch(list(_captions), batch_size=32)
                    return [(r.get("sentiment", "neutral"), float(r.get("confidence", 0.5))) for r in res]

                with st.spinner("Đang phân tích sentiment caption bằng PhoBERT..."):
                    sent_pairs = _predict_caption_sentiments(caption_texts)
                caption_sent = [x[0] for x in sent_pairs]
                caption_conf = [x[1] for x in sent_pairs]
            else:
                if not phobert_available:
                    st.info("PhoBERT chưa sẵn sàng, phần dự đoán sẽ tạm dùng sentiment = neutral.")
                caption_sent = ["neutral"] * len(df_viral)
                caption_conf = [0.5] * len(df_viral)

            df_viral["Sentiment caption"] = caption_sent
            df_viral["Sentiment conf"] = caption_conf

            sent_map = {"positive": 1.0, "neutral": 0.6, "negative": 0.35}
            df_viral["sentiment_score"] = df_viral["Sentiment caption"].map(sent_map).fillna(0.6)

            df_viral["pred_feature_score"] = (
                0.30 * df_viral["time_score"] +
                0.20 * df_viral["hashtag_score"] +
                0.20 * df_viral["caption_len_score"] +
                0.30 * df_viral["sentiment_score"]
            )

            df_viral["Pred multiplier"] = 0.7 + 0.9 * df_viral["pred_feature_score"]
            df_viral["Pred views"] = (channel_avg_views * df_viral["Pred multiplier"]).round(0)

            def _pred_level(v_pred, v_avg):
                if v_pred >= 1.2 * v_avg:
                    return "Cao"
                if v_pred >= 0.9 * v_avg:
                    return "Trung bình"
                return "Thấp"

            df_viral["Dự đoán views tương đối"] = df_viral["Pred views"].apply(lambda x: _pred_level(x, channel_avg_views))
            df_viral["Độ tin cậy dự đoán"] = (
                0.5 +
                0.3 * df_viral["Sentiment conf"] +
                0.2 * df_viral["Giờ đăng"].notna().astype(float)
            ).clip(0, 1)

            def _pred_reason(row):
                reasons = []
                if row["time_score"] >= 0.65:
                    reasons.append("khung giờ đăng có lợi")
                if 2 <= row["Số hashtag"] <= 6:
                    reasons.append("số hashtag hợp lý")
                if 40 <= row["Độ dài caption"] <= 160:
                    reasons.append("độ dài caption phù hợp")
                if row["Sentiment caption"] == "positive":
                    reasons.append("caption tích cực")
                if row["Pred multiplier"] >= 1.2:
                    reasons.append("kỳ vọng vượt avg views kênh")
                return ", ".join(reasons[:4]) if reasons else "tín hiệu trung tính"

            df_viral["Lý do dự đoán"] = df_viral.apply(_pred_reason, axis=1)

            pred_top_n = st.slider("Top N video dự đoán viral", 5, 30, 10, key="pred_viral_n")
            pred_top = df_viral.sort_values(
                ["Pred multiplier", "Độ tin cậy dự đoán", "▶ Views"],
                ascending=[False, False, False]
            ).head(pred_top_n)

            st.metric("Avg views kênh (lịch sử)", f"{channel_avg_views:,.0f}")
            st.dataframe(
                pred_top[[
                    "Chủ đề", "Mô tả", "Ngày đăng", "Nhãn giờ", "Phút đăng", "Khung giờ",
                    "Số hashtag", "Độ dài caption", "Sentiment caption",
                    "▶ Views", "Pred views", "Dự đoán views tương đối", "Độ tin cậy dự đoán", "Lý do dự đoán"
                ]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Mô tả": st.column_config.TextColumn("Mô tả", width="large"),
                    "Ngày đăng": st.column_config.TextColumn("Thứ"),
                    "Nhãn giờ": st.column_config.TextColumn("Giờ"),
                    "Phút đăng": st.column_config.NumberColumn("Phút", format="%d"),
                    "Khung giờ": st.column_config.TextColumn("Khung giờ"),
                    "Lý do dự đoán": st.column_config.TextColumn("Dựa vào đâu", width="large"),
                    "Độ tin cậy dự đoán": st.column_config.ProgressColumn(
                        "Độ tin cậy", min_value=0, max_value=1, format="%.2f"
                    ),
                },
            )


# ============================================================================
# TRANG 6: ĐÁNH GIÁ CHẤT LƯỢNG GEMINI
# ============================================================================
def page_gemini_evaluation(comments: list):
    import random

    st.title("Đánh giá chất lượng Gemini AI")
    st.caption(
        "So sánh nhãn Gemini tự động với nhãn thủ công (ground truth) "
        "→ Tính Accuracy, Precision, Recall, F1-score."
    )

    # --- Lấy các comment có nhãn thủ công làm ground truth ---
    ground_truth = [c for c in comments if c.get("method") == "manual" and c.get("sentiment")]
    n_gt = len(ground_truth)

    if n_gt < 10:
        st.warning(f"Cần ít nhất 10 nhãn thủ công để đánh giá. Hiện có: {n_gt}")
        return

    st.info(
        f"📋 Ground truth: **{n_gt} comment** đã được gán nhãn thủ công.  \n"
        "Gemini sẽ phân tích lại những comment này rồi so sánh với nhãn người gán."
    )

    # --- Cấu hình mẫu ---
    st.subheader("⚙️ Cấu hình đánh giá")
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        sample_size = st.slider(
            "Số comment lấy mẫu để đánh giá",
            min_value=10, max_value=min(200, n_gt), value=min(50, n_gt), step=10,
            help="Nhiều mẫu = kết quả chính xác hơn nhưng tốn nhiều API quota hơn"
        )
        use_stratified = st.checkbox(
            "Lấy mẫu cân bằng (stratified)",
            value=True,
            help="Đảm bảo tỷ lệ positive/neutral/negative trong mẫu bằng nhau"
        )
    with col_cfg2:
        seed = st.number_input("Random seed (để tái tạo)", value=42, step=1)
        show_errors = st.checkbox("Hiển thị các comment bị phân loại sai", value=True)

    # --- Nút chạy đánh giá ---
    st.divider()
    run_key = "eval_results"

    if st.button("▶️ Chạy đánh giá", type="primary", use_container_width=False):
        # Lấy mẫu
        random.seed(int(seed))
        if use_stratified:
            from collections import defaultdict
            by_label = defaultdict(list)
            for c in ground_truth:
                by_label[c["sentiment"]].append(c)
            labels_order = ["positive", "neutral", "negative"]
            per_label = sample_size // 3
            sample = []
            for lb in labels_order:
                pool = by_label[lb]
                take = min(per_label, len(pool))
                sample.extend(random.sample(pool, take))
            # Bổ sung nếu còn thiếu
            remaining = [c for c in ground_truth if c not in sample]
            random.shuffle(remaining)
            sample.extend(remaining[: sample_size - len(sample)])
        else:
            sample = random.sample(ground_truth, sample_size)

        st.write(f"**Mẫu:** {len(sample)} comment")

        # Phân tích bằng Gemini
        analyzer = get_gemini_analyzer_singleton()
        texts = [c["text"] for c in sample]
        y_true = [c["sentiment"] for c in sample]

        progress_bar = st.progress(0, text="Đang phân tích bằng Gemini...")
        status_placeholder = st.empty()
        y_pred = []

        def eval_progress(current, total, message):
            progress_bar.progress(current / total, text=f"Gemini đang phân tích {current}/{total}")
            status_placeholder.caption(message)

        results = analyzer.batch_analyze(texts, progress_callback=eval_progress)
        y_pred = [r["sentiment"] for r in results]

        progress_bar.empty()
        status_placeholder.empty()

        # Lưu vào session state
        st.session_state[run_key] = {
            "sample": sample,
            "y_true": y_true,
            "y_pred": y_pred,
            "results": results,
        }

    # --- Hiển thị kết quả nếu đã có ---
    if run_key not in st.session_state:
        st.caption("Nhấn **▶️ Chạy đánh giá** để bắt đầu.")
        return

    data = st.session_state[run_key]
    y_true = data["y_true"]
    y_pred = data["y_pred"]
    sample = data["sample"]
    n = len(y_true)

    LABELS = ["positive", "neutral", "negative"]
    LABEL_VI = {"positive": "Tích cực", "neutral": "Trung tính", "negative": "Tiêu cực"}

    # --- Tính metrics ---
    correct = sum(t == p for t, p in zip(y_true, y_pred))
    accuracy = correct / n if n > 0 else 0

    # Per-class precision, recall, f1
    def calc_metrics(label):
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        support   = sum(1 for t in y_true if t == label)
        return {"precision": precision, "recall": recall, "f1": f1, "support": support, "tp": tp}

    per_class = {lb: calc_metrics(lb) for lb in LABELS}
    total_support = sum(m["support"] for m in per_class.values())
    macro_f1  = sum(m["f1"]        for m in per_class.values()) / len(LABELS)
    macro_p   = sum(m["precision"] for m in per_class.values()) / len(LABELS)
    macro_r   = sum(m["recall"]    for m in per_class.values()) / len(LABELS)
    weighted_f1 = sum(m["f1"] * m["support"] for m in per_class.values()) / total_support if total_support else 0

    # --- KPI tổng quan ---
    st.divider()
    st.subheader("📊 Kết quả tổng quan")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("✅ Accuracy",       f"{accuracy*100:.1f}%",  help="(Đúng / Tổng mẫu)")
    c2.metric("🎯 Macro F1",       f"{macro_f1*100:.1f}%",  help="Trung bình F1 của 3 class")
    c3.metric("🎯 Weighted F1",    f"{weighted_f1*100:.1f}%", help="F1 có trọng số theo số mẫu")
    c4.metric("📐 Macro Precision", f"{macro_p*100:.1f}%")
    c5.metric("📏 Macro Recall",    f"{macro_r*100:.1f}%")

    # Nhận xét tự động
    st.divider()
    if accuracy >= 0.85:
        verdict = "🟢 **Gemini rất tin cậy** với tiếng Việt teen-code trên dataset này."
    elif accuracy >= 0.70:
        verdict = "🟡 **Gemini đạt mức chấp nhận được** — nên kết hợp thêm review thủ công."
    else:
        verdict = "🔴 **Gemini chưa đủ tin cậy** cho dataset này — cần nhiều nhãn thủ công hơn."
    st.info(verdict)

    # --- Classification Report ---
    st.subheader("📋 Báo cáo chi tiết theo lớp")
    report_rows = []
    for lb in LABELS:
        m = per_class[lb]
        report_rows.append({
            "Lớp": f"{LABEL_VI[lb]} ({lb})",
            "Support (GT)": m["support"],
            "Gemini đúng (TP)": m["tp"],
            "Precision": round(m["precision"], 3),
            "Recall":    round(m["recall"],    3),
            "F1-score":  round(m["f1"],        3),
        })
    report_rows.append({
        "Lớp": "**Macro avg**",
        "Support (GT)": total_support,
        "Gemini đúng (TP)": correct,
        "Precision": round(macro_p,   3),
        "Recall":    round(macro_r,   3),
        "F1-score":  round(macro_f1,  3),
    })
    df_report = pd.DataFrame(report_rows)
    st.dataframe(
        df_report, use_container_width=True, hide_index=True,
        column_config={
            "Precision": st.column_config.ProgressColumn("Precision", min_value=0, max_value=1, format="%.3f"),
            "Recall":    st.column_config.ProgressColumn("Recall",    min_value=0, max_value=1, format="%.3f"),
            "F1-score":  st.column_config.ProgressColumn("F1-score",  min_value=0, max_value=1, format="%.3f"),
        }
    )

    # --- Confusion Matrix ---
    st.subheader("🗺️ Confusion Matrix")
    cm = [[0]*3 for _ in range(3)]
    for t, p in zip(y_true, y_pred):
        if t in LABELS and p in LABELS:
            cm[LABELS.index(t)][LABELS.index(p)] += 1

    col_cm, col_bar = st.columns(2)
    with col_cm:
        fig_cm = go.Figure(data=go.Heatmap(
            z=cm,
            x=[LABEL_VI[l] for l in LABELS],
            y=[LABEL_VI[l] for l in LABELS],
            colorscale="Blues",
            text=cm,
            texttemplate="%{text}",
            textfont_size=18,
            showscale=False,
        ))
        fig_cm.update_layout(
            xaxis_title="Gemini dự đoán",
            yaxis_title="Ground truth (thủ công)",
            height=380,
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig_cm, use_container_width=True)

    with col_bar:
        st.write("**Đúng / Sai theo từng lớp**")
        bar_data = []
        for li, lb in enumerate(LABELS):
            total_lb = per_class[lb]["support"]
            tp = per_class[lb]["tp"]
            bar_data.append({"Lớp": LABEL_VI[lb], "Loại": "Đúng",  "Số lượng": tp})
            bar_data.append({"Lớp": LABEL_VI[lb], "Loại": "Sai",   "Số lượng": total_lb - tp})
        df_bar = pd.DataFrame(bar_data)
        fig_bar_chart = px.bar(
            df_bar, x="Lớp", y="Số lượng", color="Loại", barmode="stack",
            color_discrete_map={"Đúng": "#2ecc71", "Sai": "#e74c3c"},
            height=380,
        )
        st.plotly_chart(fig_bar_chart, use_container_width=True)

    # --- Phân tích lỗi phổ biến ---
    st.subheader("🔍 Phân tích lỗi (Gemini sai ở đâu?)")
    error_patterns = {}
    for t, p in zip(y_true, y_pred):
        if t != p:
            key = f"{LABEL_VI[t]} → {LABEL_VI[p]}"
            error_patterns[key] = error_patterns.get(key, 0) + 1
    if error_patterns:
        ep_df = pd.DataFrame(
            [{"Lỗi nhầm": k, "Số lần": v} for k, v in sorted(error_patterns.items(), key=lambda x: -x[1])]
        )
        col_ep, col_hint = st.columns(2)
        with col_ep:
            st.dataframe(ep_df, use_container_width=True, hide_index=True)
        with col_hint:
            most_common_err = max(error_patterns, key=error_patterns.get)
            st.warning(
                f"⚠️ Lỗi phổ biến nhất: **{most_common_err}** ({error_patterns[most_common_err]} lần)\n\n"
                "Gợi ý: Loại nhầm này thường xảy ra với comment dạng emoji, teen-code, "
                "hoặc ngữ cảnh châm biếm. Cân nhắc bổ sung vào prompt nếu cần."
            )
    else:
        st.success("🎉 Gemini không mắc lỗi nào trong mẫu này!")

    # --- Bảng chi tiết các comment bị sai ---
    if show_errors:
        wrong = [
            {"Bình luận": s["text"], "GT (thủ công)": t, "Gemini dự đoán": p}
            for s, t, p in zip(sample, y_true, y_pred) if t != p
        ]
        if wrong:
            st.subheader(f"📄 Chi tiết {len(wrong)} comment bị phân loại sai")
            df_wrong = pd.DataFrame(wrong)
            st.dataframe(
                df_wrong, use_container_width=True, hide_index=True, height=400,
                column_config={
                    "Bình luận": st.column_config.TextColumn("Bình luận", width="large"),
                    "GT (thủ công)": st.column_config.TextColumn("Ground Truth", width="small"),
                    "Gemini dự đoán": st.column_config.TextColumn("Gemini", width="small"),
                }
            )
            # Xuất file
            buf = io.BytesIO()
            df_wrong.to_excel(buf, index=False, engine="openpyxl")
            buf.seek(0)
            st.download_button(
                "⬇️ Tải danh sách lỗi (Excel)",
                data=buf,
                file_name=f"gemini_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # --- Xuất báo cáo tổng hợp ---
    st.divider()
    if st.button("📑 Xuất báo cáo đánh giá (Excel)"):
        rows_out = []
        for s, t, p, r in zip(sample, y_true, y_pred, data["results"]):
            rows_out.append({
                "text": s["text"],
                "ground_truth": t,
                "gemini_pred": p,
                "gemini_confidence": r["confidence"],
                "correct": t == p,
            })
        df_out = pd.DataFrame(rows_out)
        buf2 = io.BytesIO()
        df_out.to_excel(buf2, index=False, engine="openpyxl")
        buf2.seek(0)
        fname = f"gemini_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        st.download_button(
            f"⬇️ Tải báo cáo: {fname}",
            data=buf2, file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ============================================================================
# TRANG: TIỀN XỬ LÝ TEXT
# ============================================================================
def page_text_preprocessing(comments: list):
    st.title("Tiền xử lý Text")
    st.caption(
        "Chuẩn hóa teen-code, emoji → text, loại bỏ comment vô giá trị và duplicate. "
        "Giúp cải thiện độ chính xác khi phân tích sentiment."
    )

    if not _PREPROCESSOR_OK:
        st.error("Không tìm thấy `modules/text_preprocessor.py`. Kiểm tra lại cài đặt.")
        return

    # ── Tab: Demo thử nghiệm / Xử lý toàn bộ / Từ điển ──────────────────
    tab_demo, tab_batch, tab_dict = st.tabs([
        "Thử nghiệm", "Xử lý toàn bộ dataset", "Từ điển"
    ])

    # ── TAB 1: DEMO ────────────────────────────────────────────────────────
    with tab_demo:
        st.subheader("Nhập comment để xem kết quả tiền xử lý")

        sample_texts = [
            "Ủa k hiểu mn ơi 😭 trường này dc k ạ",
            "tvu oce nha ae 🔥🔥 đỉnh vcl",
            "hp cao quá k chịu nổi 😤 sv khổ lắm",
            "ok 👍",
            "haha hihi",
            "Học bổng hb năm nay đc bao nhiêu % vậy mn",
        ]
        example = st.selectbox("Chọn ví dụ có sẵn (hoặc nhập bên dưới)", ["-- Nhập tay --"] + sample_texts)
        input_text = st.text_area(
            "Comment cần xử lý",
            value="" if example == "-- Nhập tay --" else example,
            height=80,
        )

        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            do_teen  = st.checkbox("Chuẩn hóa teen-code", value=True)
        with col_opt2:
            do_emoji = st.checkbox("Chuyển emoji → text", value=True)

        if input_text.strip():
            from modules.text_preprocessor import preprocess, is_low_value
            cleaned = preprocess(input_text, normalize_teen=do_teen, normalize_emojis=do_emoji)
            low_val = is_low_value(input_text)

            col_in, col_out = st.columns(2)
            with col_in:
                st.markdown("**📥 Gốc:**")
                st.info(input_text)
            with col_out:
                st.markdown("**📤 Sau xử lý:**")
                if low_val:
                    st.warning(f"⚠️ Comment vô giá trị — sẽ bị loại bỏ")
                else:
                    st.success(cleaned)

            if not low_val and cleaned != input_text:
                changed_words = []
                orig_words  = input_text.split()
                clean_words = cleaned.split()
                st.caption(f"Số từ: {len(orig_words)} → {len(clean_words)}")

    # ── TAB 2: XỬ LÝ TOÀN BỘ ──────────────────────────────────────────────
    with tab_batch:
        st.subheader("Xử lý toàn bộ dataset hiện tại")

        if not comments:
            st.warning("Không có comment nào trong dataset.")
        else:
            st.write(f"Dataset hiện tại: **{len(comments)} comment**")

            col_cfg1, col_cfg2 = st.columns(2)
            with col_cfg1:
                batch_teen  = st.checkbox("Chuẩn hóa teen-code", value=True, key="batch_teen")
                batch_emoji = st.checkbox("Chuyển emoji → text",  value=True, key="batch_emoji")
            with col_cfg2:
                batch_lowval = st.checkbox("Loại comment vô giá trị", value=True, key="batch_low")
                batch_dup    = st.checkbox("Loại duplicate",           value=True, key="batch_dup")

            if st.button("▶️ Chạy tiền xử lý", type="primary"):
                from modules.text_preprocessor import TextPreprocessor
                proc = TextPreprocessor(
                    normalize_teen=batch_teen,
                    normalize_emojis=batch_emoji,
                    remove_low_value=batch_lowval,
                    remove_duplicates=batch_dup,
                )
                result = proc.process_comments(comments)
                st.session_state["preproc_result"] = result

            if "preproc_result" in st.session_state:
                r = st.session_state["preproc_result"]
                s = r["stats"]

                # KPI
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("✅ Giữ lại",         s["kept"])
                c2.metric("🗑️ Vô giá trị",      s["removed_low_value"])
                c3.metric("♻️ Duplicate",        s["removed_duplicate"])
                c4.metric("📉 Tỉ lệ loại bỏ",   f"{s['reduction_rate_pct']}%")

                # Xem trước kết quả
                st.subheader("Xem trước 20 comment sau xử lý")
                preview = []
                for c in r["processed"][:20]:
                    preview.append({
                        "Gốc":           c.get("text_original", ""),
                        "Sau xử lý":     c.get("text", ""),
                        "Sentiment":     c.get("sentiment", ""),
                    })
                df_prev = pd.DataFrame(preview)
                st.dataframe(
                    df_prev, use_container_width=True, hide_index=True,
                    column_config={
                        "Gốc":       st.column_config.TextColumn(width="large"),
                        "Sau xử lý": st.column_config.TextColumn(width="large"),
                    }
                )

                # Xem comment bị loại
                with st.expander(f"🗑️ {s['removed_low_value']} comment vô giá trị bị loại"):
                    if r["removed_low_value"]:
                        df_low = pd.DataFrame([
                            {"Text": c.get("text", ""), "Lý do": c.get("removal_reason", "")}
                            for c in r["removed_low_value"][:50]
                        ])
                        st.dataframe(df_low, use_container_width=True, hide_index=True)
                    else:
                        st.caption("Không có comment nào bị loại theo tiêu chí này.")

                with st.expander(f"♻️ {s['removed_duplicate']} comment duplicate bị loại"):
                    if r["removed_duplicate"]:
                        df_dup = pd.DataFrame([
                            {"Text": c.get("text_original", c.get("text", ""))}
                            for c in r["removed_duplicate"][:50]
                        ])
                        st.dataframe(df_dup, use_container_width=True, hide_index=True)
                    else:
                        st.caption("Không phát hiện duplicate nào.")

                # Xuất kết quả
                buf = io.BytesIO()
                df_export = pd.DataFrame([
                    {
                        "text_original": c.get("text_original", ""),
                        "text_cleaned":  c.get("text", ""),
                        "sentiment":     c.get("sentiment", ""),
                        "method":        c.get("method", ""),
                        "author":        c.get("author", ""),
                        "likes":         c.get("likes", 0),
                        "video_id":      c.get("video_id", ""),
                    }
                    for c in r["processed"]
                ])
                df_export.to_excel(buf, index=False, engine="openpyxl")
                buf.seek(0)
                st.download_button(
                    "⬇️ Tải dataset đã tiền xử lý (Excel)",
                    data=buf,
                    file_name=f"comments_preprocessed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

    # ── TAB 3: TỪ ĐIỂN ────────────────────────────────────────────────────
    with tab_dict:
        st.subheader("📖 Từ điển Teen-code & Emoji")

        col_tc, col_em = st.columns(2)
        with col_tc:
            st.markdown("**Teen-code → Từ chuẩn**")
            search_teen = st.text_input("Tìm kiếm", key="search_teen", placeholder="vd: k, mn, sv...")
            rows_tc = [{"Teen-code": k, "Từ chuẩn": v} for k, v in TEENCODE_DICT.items()]
            if search_teen:
                rows_tc = [r for r in rows_tc if search_teen.lower() in r["Teen-code"] or search_teen.lower() in r["Từ chuẩn"]]
            st.dataframe(pd.DataFrame(rows_tc), use_container_width=True, hide_index=True, height=400)
            st.caption(f"Tổng: {len(TEENCODE_DICT)} từ")

        with col_em:
            st.markdown("**Emoji → Mô tả cảm xúc**")
            rows_em = [{"Emoji": k, "Mô tả": v.strip()} for k, v in EMOJI_SENTIMENT.items()]
            st.dataframe(pd.DataFrame(rows_em), use_container_width=True, hide_index=True, height=400)
            st.caption(f"Tổng: {len(EMOJI_SENTIMENT)} emoji")

        st.info(
            "💡 Muốn thêm từ mới? Mở file `modules/text_preprocessor.py`, "
            "tìm `TEENCODE_DICT` hoặc `EMOJI_SENTIMENT` và thêm vào."
        )


# ============================================================================
# TRANG: PHOBERT FINE-TUNED
# ============================================================================
def page_phobert(comments: list):
    st.title("PhoBERT Fine-tuned")
    st.caption("Model PhoBERT được fine-tune trên comment TikTok @travinhuniversity — phân tích sentiment tiếng Việt")

    model_ready = _PHOBERT_IMPORTABLE and is_model_available()

    # ── Trạng thái model ──────────────────────────────────────────────────────
    if not model_ready:
        st.warning("⚠️ Model chưa được cài đặt.")
        with st.expander("📋 Hướng dẫn cài đặt model", expanded=True):
            st.markdown("""
**Bước 1 — Chạy notebook trên Google Colab:**
```
tiktok_analytics/phobert_finetune.ipynb
```

**Bước 2 — Tải file về:**
Sau khi train xong, Colab tự tải `phobert_tvu_sentiment.zip` về máy.

**Bước 3 — Giải nén vào project:**
```
tiktok_analytics/
  models/
    phobert_tvu_sentiment/    ← giải nén vào đây
      config.json
      model.safetensors
      tokenizer_config.json
      special_tokens_map.json
      vocab.txt
      training_metadata.json
```

**Bước 4 — Cài thư viện (nếu chưa có):**
```powershell
pip install torch transformers
```

**Bước 5 — Khởi động lại Streamlit**, trang này sẽ tự nhận model.
""")
        st.info("📓 Xem `phobert_finetune.ipynb` trong project để bắt đầu fine-tune.")
        return

    # ── Load model (cache) ───────────────────────────────────────────────────
    @st.cache_resource
    def load_phobert():
        return PhoBERTSentiment()

    with st.spinner("Đang tải PhoBERT model..."):
        analyzer = load_phobert()

    info = analyzer.info()

    # ── KPIs ─────────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Test Accuracy", f"{info['test_accuracy']*100:.1f}%" if info['test_accuracy'] else "N/A")
    col2.metric("Test F1", f"{info['test_f1']:.4f}" if info['test_f1'] else "N/A")
    col3.metric("Best Val F1", f"{info['best_val_f1']:.4f}" if info['best_val_f1'] else "N/A")
    col4.metric("Train size", str(info['train_size']) if info['train_size'] else "N/A")
    st.caption(f"Model: `{info['model_path']}` | Device: `{info['device']}` | Epochs: {info['epochs']}")
    if info.get('test_size'):
        st.caption(
            f"Nguồn train: `{info.get('fine_tuned_on') or 'N/A'}` | "
            f"Split train/val/test: {info.get('train_size') or 'N/A'}/"
            f"{info.get('val_size') or 'N/A'}/{info.get('test_size')}"
        )
    st.info(
        "Lưu ý: KPI phía trên (Test Accuracy/F1) là kết quả trên **test split lúc huấn luyện**. "
        "Ở tab so sánh bên dưới, model được chạy trên **tập manual hiện tại trong dashboard**, "
        "nên số liệu có thể khác đáng kể."
    )
    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Demo", "Phân tích toàn bộ", "So sánh với Gemini", "Dự đoán chưa có nhãn", "So sánh Wonrax vs Fine-tuned"])

    # ── Tab 1: Demo ───────────────────────────────────────────────────────────
    with tab1:
        st.subheader("Thử nghiệm comment mới")
        demo_input = st.text_area(
            "Nhập comment tiếng Việt:",
            placeholder="k thích ktx lắm, hp cao quá 😤",
            height=100
        )
        if st.button("🔍 Phân tích", type="primary"):
            if demo_input.strip():
                with st.spinner("Đang phân tích..."):
                    result = analyzer.predict(demo_input)
                sent = result['sentiment']
                conf = result['confidence']
                emoji_map = {'positive': '😊', 'neutral': '😐', 'negative': '😞'}
                color_map  = {'positive': 'green', 'neutral': 'orange', 'negative': 'red'}

                st.markdown(f"### Kết quả: {emoji_map[sent]} :{color_map[sent]}[**{sent.upper()}**] ({conf:.0%})")

                col_s, col_c = st.columns([1, 1])
                with col_s:
                    st.markdown("**Điểm số:**")
                    for lbl, score in result['scores'].items():
                        bar = "█" * int(score * 20)
                        st.markdown(f"`{lbl:8s}` {bar} {score:.2%}")
                with col_c:
                    st.markdown("**Text sau tiền xử lý:**")
                    st.code(result['text_clean'] or "(trống)", language=None)
            else:
                st.warning("Vui lòng nhập comment.")

        st.divider()
        st.subheader("Ví dụ nhanh")
        st.caption("Ví dụ lấy từ dữ liệu đã gán nhãn thủ công để đối chiếu trực tiếp với PhoBERT.")

        df_quick = _prepare_comments_df(comments)
        if not df_quick.empty:
            df_quick = df_quick[
                (df_quick["sentiment"].isin(VALID_SENTIMENTS)) &
                (df_quick["method"] == "manual")
            ].copy()

        if df_quick.empty:
            st.info("Chưa có dữ liệu nhãn thủ công để tạo ví dụ nhanh.")
        else:
            # Lấy tối đa 2 ví dụ mỗi lớp để cân bằng positive/neutral/negative.
            sample_df = (
                df_quick.groupby("sentiment", group_keys=False)
                .head(2)
                .reset_index(drop=True)
            )
            sample_df["preview"] = sample_df["text"].fillna("").astype(str).str.slice(0, 70)
            sample_df["label"] = sample_df["preview"] + "  [manual=" + sample_df["sentiment"] + "]"

            selected_idx = st.selectbox(
                "Chọn ví dụ để test nhanh",
                options=sample_df.index.tolist(),
                format_func=lambda i: sample_df.loc[i, "label"],
                key="phobert_quick_example_select"
            )

            selected_text = str(sample_df.loc[selected_idx, "text"])
            expected = str(sample_df.loc[selected_idx, "sentiment"])

            if st.button("▶ Chạy ví dụ đã chọn", key="phobert_quick_example_run"):
                result = analyzer.predict(selected_text)
                sent = result['sentiment']
                icon = "✅" if sent == expected else "❌"
                st.write(
                    f"{icon} **PhoBERT: {sent}** ({result['confidence']:.0%}) | "
                    f"**Nhãn thủ công: {expected}**"
                )
                st.code(selected_text, language=None)

    # ── Tab 2: Phân tích toàn bộ ──────────────────────────────────────────────
    with tab2:
        st.subheader("Phân tích toàn bộ dataset với PhoBERT")

        df = pd.DataFrame(comments)
        if df.empty or 'text' not in df.columns:
            st.error("Không có dữ liệu comment.")
        else:
            n = len(df)
            st.info(f"Sẽ phân tích **{n} comments** bằng PhoBERT fine-tuned.")
            if st.button("🚀 Bắt đầu phân tích batch", type="primary"):
                progress_bar = st.progress(0)
                status_text  = st.empty()

                def on_progress(done, total):
                    pct = done / total
                    progress_bar.progress(pct)
                    status_text.text(f"Đang xử lý {done}/{total} comments...")

                texts = df['text'].fillna('').tolist()
                with st.spinner("PhoBERT đang phân tích..."):
                    results = analyzer.predict_batch(texts, batch_size=32, progress_callback=on_progress)

                progress_bar.progress(1.0)
                status_text.text("✅ Hoàn tất!")

                pred_df = pd.DataFrame(results)
                df['phobert_sentiment']   = pred_df['sentiment'].values
                df['phobert_confidence']  = pred_df['confidence'].values

                # KPI
                total = len(df)
                pos = (df['phobert_sentiment'] == 'positive').sum()
                neu = (df['phobert_sentiment'] == 'neutral').sum()
                neg = (df['phobert_sentiment'] == 'negative').sum()
                c1, c2, c3 = st.columns(3)
                c1.metric("😊 Positive", f"{pos} ({pos/total:.0%})")
                c2.metric("😐 Neutral",  f"{neu} ({neu/total:.0%})")
                c3.metric("😞 Negative", f"{neg} ({neg/total:.0%})")

                # Chart
                fig = px.pie(
                    names=['positive', 'neutral', 'negative'],
                    values=[pos, neu, neg],
                    color=['positive', 'neutral', 'negative'],
                    color_discrete_map={'positive': '#4CAF50', 'neutral': '#FFC107', 'negative': '#F44336'},
                    title="PhoBERT Sentiment Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)

                # Table
                show_df = df[['text', 'phobert_sentiment', 'phobert_confidence']].copy()
                show_df.columns = ['Nội dung', 'Sentiment (PhoBERT)', 'Confidence']
                st.dataframe(show_df, use_container_width=True, hide_index=True)

                # Export
                buf = io.BytesIO()
                df.to_excel(buf, index=False, engine='openpyxl')
                buf.seek(0)
                st.download_button(
                    "📥 Tải kết quả Excel",
                    data=buf,
                    file_name=f"phobert_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    # ── Tab 3: So sánh với Gemini ─────────────────────────────────────────────
    with tab3:
        st.subheader("So sánh PhoBERT vs nhãn thủ công")
        df_cmp = pd.DataFrame(comments)

        # Chỉ lấy những comment có nhãn manual để so sánh
        if 'sentiment' not in df_cmp.columns or df_cmp.empty:
            st.warning("Không có nhãn gốc để so sánh.")
        else:
            df_cmp = df_cmp[df_cmp['sentiment'].isin(['positive', 'neutral', 'negative'])].copy()
            n_cmp = len(df_cmp)
            st.info(f"Sẽ so sánh trên **{n_cmp} comments** có nhãn gốc.")

            if st.button("🔄 Chạy so sánh", key="cmp_btn"):
                texts_cmp = df_cmp['text'].fillna('').tolist()
                with st.spinner(f"PhoBERT phân tích {n_cmp} comments..."):
                    results_cmp = analyzer.predict_batch(texts_cmp, batch_size=32)

                df_cmp['phobert_pred'] = [r['sentiment'] for r in results_cmp]
                df_cmp['phobert_conf'] = [r['confidence'] for r in results_cmp]

                # Accuracy
                correct = (df_cmp['sentiment'] == df_cmp['phobert_pred']).sum()
                acc = correct / n_cmp

                from sklearn.metrics import f1_score, classification_report
                labels_true = df_cmp['sentiment'].tolist()
                labels_pred = df_cmp['phobert_pred'].tolist()
                f1 = f1_score(labels_true, labels_pred, average='weighted', zero_division=0)

                c1, c2, c3 = st.columns(3)
                c1.metric("Accuracy vs Manual", f"{acc:.2%}")
                c2.metric("F1-score (weighted)", f"{f1:.4f}")
                c3.metric("Sai", f"{n_cmp - correct} ({1-acc:.0%})")

                # Report
                report = classification_report(labels_true, labels_pred,
                                               target_names=['negative', 'neutral', 'positive'],
                                               zero_division=0)
                st.text("Classification Report:")
                st.code(report)

                # Confusion matrix
                from sklearn.metrics import confusion_matrix
                import plotly.figure_factory as ff
                label_order = ['positive', 'neutral', 'negative']
                cm = confusion_matrix(labels_true, labels_pred, labels=label_order)
                cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)

                fig_cm = go.Figure(data=go.Heatmap(
                    z=cm_norm,
                    x=[f"Pred {l}" for l in label_order],
                    y=[f"True {l}" for l in label_order],
                    colorscale='RdYlGn',
                    text=[[f"{cm[i][j]}<br>({cm_norm[i][j]:.0%})" for j in range(3)] for i in range(3)],
                    texttemplate="%{text}",
                ))
                fig_cm.update_layout(title="Confusion Matrix — PhoBERT vs Manual Labels", height=400)
                st.plotly_chart(fig_cm, use_container_width=True)

                # Sai lệch
                df_wrong = df_cmp[df_cmp['sentiment'] != df_cmp['phobert_pred']][
                    ['text', 'sentiment', 'phobert_pred', 'phobert_conf']
                ].copy()
                df_wrong.columns = ['Nội dung', 'Nhãn thực', 'PhoBERT dự đoán', 'Confidence']
                st.markdown(f"**❌ {len(df_wrong)} comment dự đoán sai:**")
                st.dataframe(df_wrong.head(20), use_container_width=True, hide_index=True)

    # ── Tab 4: Dự đoán comment chưa có nhãn ──────────────────────────────────
    with tab4:
        st.subheader("Dự đoán comment chưa có nhãn")
        st.caption(
            "PhoBERT tự động gán nhãn sentiment cho các comment chưa được gán thủ công, "
            "sau đó lưu kết quả thẳng vào `tong_hop_comment.json`."
        )

        # Load từ file nguồn để đếm chính xác
        try:
            comment_data_src = load_comment_source()
        except Exception as e:
            st.error(f"Không thể đọc file dữ liệu nguồn: {e}")
            return

        all_src_comments = []
        for video in comment_data_src.get("videos", []):
            all_src_comments.extend(video.get("comments", []))

        manual_comments   = [c for c in all_src_comments if str(c.get("method", "")).strip().lower() == "manual"]
        phobert_comments  = [c for c in all_src_comments if str(c.get("method", "")).strip().lower() == "phobert"]
        truly_unlabeled   = [
            c for c in all_src_comments
            if str(c.get("method", "")).strip().lower() not in ("manual", "phobert", "gemini")
            and str(c.get("sentiment", "")).strip().lower() not in VALID_SENTIMENTS
        ]
        other_auto        = [
            c for c in all_src_comments
            if str(c.get("method", "")).strip().lower() not in ("manual", "phobert", "gemini")
            and str(c.get("sentiment", "")).strip().lower() in VALID_SENTIMENTS
        ]

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Tổng comment nguồn",   len(all_src_comments))
        mc2.metric("Nhãn thủ công",         len(manual_comments),   help="method = manual")
        mc3.metric("Đã dự đoán (PhoBERT)", len(phobert_comments),  help="method = phobert")
        mc4.metric("Chưa có nhãn",          len(truly_unlabeled),   help="Chưa có nhãn hợp lệ và không phải manual/phobert/gemini")

        st.divider()

        # Tuỳ chọn dự đoán lại PhoBERT cũ
        include_repred = st.checkbox(
            "Bao gồm cả comment đã có nhãn PhoBERT (dự đoán lại)",
            value=False,
            key="phobert_repred_chk"
        )
        auto_update_dashboard = st.checkbox(
            "Tự động cập nhật dữ liệu dashboard ngay sau khi dự đoán",
            value=True,
            key="phobert_auto_update_chk",
            help="Nếu bật, kết quả PhoBERT sẽ được lưu ngay vào dữ liệu và dashboard tự tải lại."
        )
        to_predict_list = (truly_unlabeled + phobert_comments) if include_repred else truly_unlabeled

        if not to_predict_list:
            st.success("✅ Tất cả comment đã có nhãn! Không còn gì để dự đoán.")
        else:
            st.info(f"Sẽ dự đoán **{len(to_predict_list)} comments** bằng PhoBERT fine-tuned.")

            if st.button(
                f"🚀 Bắt đầu dự đoán {len(to_predict_list)} comments",
                type="primary",
                key="phobert_predict_btn"
            ):
                prog_bar   = st.progress(0)
                status_txt = st.empty()

                def _on_progress(done, total):
                    prog_bar.progress(done / total)
                    status_txt.text(f"Đang xử lý {done}/{total}…")

                texts_to_pred = [c.get("text", "") or "" for c in to_predict_list]
                with st.spinner("PhoBERT đang phân tích…"):
                    pred_results = analyzer.predict_batch(
                        texts_to_pred, batch_size=32, progress_callback=_on_progress
                    )

                prog_bar.progress(1.0)
                status_txt.success(f"✅ Hoàn tất {len(pred_results)} comments!")

                # Build updates dict (key → prediction)
                batch_updates = {}
                for comment, result in zip(to_predict_list, pred_results):
                    key = _comment_key(comment)
                    batch_updates[key] = {
                        "sentiment":  result["sentiment"],
                        "confidence": result["confidence"],
                        "method":     "phobert",
                    }

                batch_rows = [
                    {
                        "text":       c.get("text", ""),
                        "sentiment":  r["sentiment"],
                        "confidence": r["confidence"],
                        "pos":        r["scores"]["positive"],
                        "neu":        r["scores"]["neutral"],
                        "neg":        r["scores"]["negative"],
                    }
                    for c, r in zip(to_predict_list, pred_results)
                ]

                if auto_update_dashboard:
                    with st.spinner("Đang cập nhật dữ liệu dashboard…"):
                        saved_count = _persist_prediction_updates(batch_updates, comments)
                    st.success(
                        f"✅ Đã cập nhật **{saved_count}** comment vào dữ liệu. "
                        "Dashboard sẽ tự tải lại để phản ánh kết quả mới."
                    )
                    st.session_state.pop("phobert_batch_updates", None)
                    st.session_state.pop("phobert_batch_rows", None)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.session_state["phobert_batch_updates"] = batch_updates
                    st.session_state["phobert_batch_rows"] = batch_rows

        # Hiển thị kết quả nếu đã có trong session state
        if st.session_state.get("phobert_batch_rows"):
            rows  = st.session_state["phobert_batch_rows"]
            total_r = len(rows)
            pos_r = sum(1 for r in rows if r["sentiment"] == "positive")
            neu_r = sum(1 for r in rows if r["sentiment"] == "neutral")
            neg_r = sum(1 for r in rows if r["sentiment"] == "negative")

            st.divider()
            st.markdown("#### Kết quả dự đoán")
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric("😊 Positive", f"{pos_r}",  f"{pos_r/total_r:.1%}")
            rc2.metric("😐 Neutral",  f"{neu_r}",  f"{neu_r/total_r:.1%}")
            rc3.metric("😞 Negative", f"{neg_r}",  f"{neg_r/total_r:.1%}")

            fig_pred = px.pie(
                names=["positive", "neutral", "negative"],
                values=[pos_r, neu_r, neg_r],
                color=["positive", "neutral", "negative"],
                color_discrete_map={"positive": "#4CAF50", "neutral": "#FFC107", "negative": "#F44336"},
                title=f"PhoBERT — Phân phối sentiment ({total_r} comments chưa có nhãn)",
                hole=0.4,
            )
            fig_pred.update_traces(textinfo="percent+label+value", textfont_size=13)
            fig_pred.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_pred, use_container_width=True)

            df_pred_show = pd.DataFrame([
                {
                    "Nội dung":    r["text"][:90] + ("…" if len(r["text"]) > 90 else ""),
                    "Sentiment":   r["sentiment"],
                    "Confidence":  f"{r['confidence']:.0%}",
                    "😊 Pos":      f"{r['pos']:.0%}",
                    "😐 Neu":      f"{r['neu']:.0%}",
                    "😞 Neg":      f"{r['neg']:.0%}",
                }
                for r in rows
            ])
            st.dataframe(df_pred_show, use_container_width=True, hide_index=True)

            # Nút tải Excel
            buf_pred = io.BytesIO()
            pd.DataFrame([
                {"text": r["text"], "sentiment": r["sentiment"], "confidence": r["confidence"]}
                for r in rows
            ]).to_excel(buf_pred, index=False, engine="openpyxl")
            buf_pred.seek(0)
            st.download_button(
                "📥 Tải kết quả Excel",
                data=buf_pred,
                file_name=f"phobert_unlabeled_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="phobert_dl_btn"
            )

            # Nút lưu vào dữ liệu
            st.divider()
            n_upd = len(st.session_state.get("phobert_batch_updates", {}))
            st.markdown(
                f"**💾 Lưu {n_upd} nhãn PhoBERT vào dữ liệu** — "
                "cập nhật `tong_hop_comment.json` và merged file. "
                "Thao tác **không ảnh hưởng** đến nhãn thủ công (method=manual)."
            )
            if st.button("💾 Lưu kết quả vào dữ liệu", type="secondary", key="phobert_save_btn"):
                updates_to_save = st.session_state.get("phobert_batch_updates", {})
                if updates_to_save:
                    with st.spinner("Đang lưu vào dữ liệu…"):
                        saved_count = _persist_prediction_updates(updates_to_save, comments)
                    st.success(f"✅ Đã lưu **{saved_count}** nhãn PhoBERT vào dữ liệu!")
                    st.session_state.pop("phobert_batch_updates", None)
                    st.session_state.pop("phobert_batch_rows", None)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Không có dữ liệu để lưu. Hãy chạy dự đoán trước.")

    # ── Tab 5: So sánh Wonrax vs Fine-tuned ──────────────────────────────────
    with tab5:
        st.subheader("Wonrax (general) vs PhoBERT Fine-tuned (TVU)")
        st.caption(
            "Đo accuracy/F1 của **wonrax/phobert-base-vietnamese-sentiment** (model huấn luyện sẵn) "
            "và **PhoBERT fine-tuned** trên cùng tập comment TVU có nhãn thủ công, "
            "để đánh giá mức độ cải thiện sau khi fine-tune."
        )

        # Lấy comment có nhãn thủ công làm ground truth
        df_cmp5 = pd.DataFrame(comments)
        if df_cmp5.empty or 'sentiment' not in df_cmp5.columns:
            st.error("Không có dữ liệu.")
        else:
            df_cmp5 = df_cmp5[
                df_cmp5['sentiment'].isin(VALID_SENTIMENTS) &
                (df_cmp5['method'].astype(str).str.lower() == 'manual')
            ].copy()

            n5 = len(df_cmp5)
            test_size_meta = info.get('test_size')
            st.info(
                f"Sẽ so sánh trên **{n5} comments có nhãn thủ công** (method=manual) — đây là ground truth."
            )
            if test_size_meta:
                st.warning(
                    f"Đây KHÔNG phải test split lúc train (test_size metadata = {test_size_meta}). "
                    f"Bạn đang đánh giá trên tập manual hiện tại (n={n5}), nên kết quả có thể khác KPI phía trên."
                )

            if st.button("🔄 Chạy so sánh Wonrax vs Fine-tuned", type="primary", key="cmp5_btn"):
                texts5 = df_cmp5['text'].fillna('').tolist()
                labels_true5 = df_cmp5['sentiment'].tolist()

                # ── Bước 1: Fine-tuned model ─────────────────────────────────
                with st.spinner("PhoBERT fine-tuned đang phân tích..."):
                    results_ft = analyzer.predict_batch(texts5, batch_size=32)
                preds_ft = [r['sentiment'] for r in results_ft]

                # ── Bước 2: Wonrax model ─────────────────────────────────────
                @st.cache_resource(show_spinner=False)
                def load_wonrax():
                    import torch
                    from transformers import AutoTokenizer, AutoModelForSequenceClassification
                    from pathlib import Path

                    _MODEL_ID   = 'wonrax/phobert-base-vietnamese-sentiment'
                    _LOCAL_CACHE = Path('models') / 'wonrax_cache'

                    def _move_to_gpu(mdl):
                        mdl.eval()
                        if torch.cuda.is_available():
                            mdl = mdl.cuda()
                        return mdl

                    # ── 1. Local safetensors cache (tải lần sau, nhanh) ───────
                    if (_LOCAL_CACHE / 'model.safetensors').exists() and \
                       (_LOCAL_CACHE / 'config.json').exists():
                        try:
                            tok = AutoTokenizer.from_pretrained(str(_LOCAL_CACHE))
                            mdl = AutoModelForSequenceClassification.from_pretrained(
                                str(_LOCAL_CACHE), use_safetensors=True
                            )
                            return tok, _move_to_gpu(mdl), None
                        except Exception:
                            pass  # Cache hỏng → thử lại từ HF

                    # ── 2. Tải từ HuggingFace với safetensors=True ────────────
                    _err1 = None
                    try:
                        tok = AutoTokenizer.from_pretrained(_MODEL_ID)
                        mdl = AutoModelForSequenceClassification.from_pretrained(
                            _MODEL_ID, use_safetensors=True
                        )
                        # Lưu cache local để lần sau dùng safetensors
                        _LOCAL_CACHE.mkdir(parents=True, exist_ok=True)
                        tok.save_pretrained(str(_LOCAL_CACHE))
                        mdl.save_pretrained(str(_LOCAL_CACHE), safe_serialization=True)
                        return tok, _move_to_gpu(mdl), None
                    except Exception as e:
                        _err1 = e

                    # ── 3. Workaround: patch torch.__version__ để bypass ──────
                    # CVE-2025-32434 chặn torch.load trên torch < 2.6.
                    # Wonrax là model public đáng tin cậy → patch an toàn,
                    # sau đó ngay lập tức convert sang safetensors và lưu cache.
                    _err2 = None
                    try:
                        _orig_ver = torch.__version__
                        try:
                            torch.__version__ = '2.6.0+cu121'
                            tok = AutoTokenizer.from_pretrained(_MODEL_ID)
                            mdl = AutoModelForSequenceClassification.from_pretrained(
                                _MODEL_ID
                            )
                        finally:
                            torch.__version__ = _orig_ver  # Khôi phục ngay

                        # Convert sang safetensors để lần sau không cần patch
                        _LOCAL_CACHE.mkdir(parents=True, exist_ok=True)
                        tok.save_pretrained(str(_LOCAL_CACHE))
                        mdl.save_pretrained(str(_LOCAL_CACHE), safe_serialization=True)
                        return tok, _move_to_gpu(mdl), None
                    except Exception as e:
                        _err2 = e

                    return None, None, (
                        f"Không thể tải wonrax.\n"
                        f"• safetensors: {_err1}\n"
                        f"• workaround : {_err2}\n\n"
                        f"Giải pháp bền vững: nâng cấp torch lên 2.6+\n"
                        f"  pip install torch --upgrade --index-url "
                        f"https://download.pytorch.org/whl/cu121"
                    )

                with st.spinner("Đang tải wonrax model (lần đầu ~400MB, tự lưu cache safetensors)..."):
                    wonrax_tok, wonrax_mdl, wonrax_err = load_wonrax()

                if wonrax_tok is None:
                    st.error(f"Không thể tải wonrax:\n```\n{wonrax_err}\n```")
                    st.info(
                        "**Giải pháp nhanh:** Nâng cấp PyTorch lên 2.6+\n"
                        "```powershell\n"
                        "pip install torch --upgrade "
                        "--index-url https://download.pytorch.org/whl/cu121\n"
                        "```"
                    )
                else:
                    import torch
                    import torch.nn.functional as F_wr
                    # wonrax label order: [NEG, NEU, POS] → index 0=neg,1=neu,2=pos
                    _WR_LABELS = ['negative', 'neutral', 'positive']
                    _device_wr = next(wonrax_mdl.parameters()).device

                    preds_wr = []
                    conf_wr  = []
                    batch_sz = 32
                    prog5 = st.progress(0)
                    stat5 = st.empty()
                    for i in range(0, len(texts5), batch_sz):
                        batch = texts5[i:i + batch_sz]
                        enc = wonrax_tok(
                            batch,
                            return_tensors='pt',
                            truncation=True,
                            max_length=256,
                            padding=True
                        )
                        enc = {k: v.to(_device_wr) for k, v in enc.items()}
                        with torch.no_grad():
                            logits = wonrax_mdl(**enc).logits
                        probs = F_wr.softmax(logits, dim=1).cpu().numpy()
                        for p in probs:
                            idx = int(p.argmax())
                            preds_wr.append(_WR_LABELS[idx])
                            conf_wr.append(float(p[idx]))
                        done5 = min(i + batch_sz, len(texts5))
                        prog5.progress(done5 / len(texts5))
                        stat5.text(f"Wonrax: {done5}/{len(texts5)}...")
                    prog5.progress(1.0)
                    stat5.success("✅ Wonrax hoàn tất!")

                    st.session_state['cmp5_true']    = labels_true5
                    st.session_state['cmp5_ft']      = preds_ft
                    st.session_state['cmp5_wr']      = preds_wr
                    st.session_state['cmp5_conf_wr'] = conf_wr
                    st.session_state['cmp5_conf_ft'] = [r['confidence'] for r in results_ft]

        # Hiển thị kết quả so sánh
        if st.session_state.get('cmp5_true'):
            from sklearn.metrics import (
                accuracy_score, f1_score, classification_report, confusion_matrix
            )

            y_true = st.session_state['cmp5_true']
            y_ft   = st.session_state['cmp5_ft']
            y_wr   = st.session_state['cmp5_wr']
            conf_ft = st.session_state['cmp5_conf_ft']
            conf_wr = st.session_state['cmp5_conf_wr']
            n_cmp5  = len(y_true)

            acc_ft  = accuracy_score(y_true, y_ft)
            acc_wr  = accuracy_score(y_true, y_wr)
            f1_ft_w = f1_score(y_true, y_ft, average='weighted', zero_division=0)
            f1_wr_w = f1_score(y_true, y_wr, average='weighted', zero_division=0)
            f1_ft_m = f1_score(y_true, y_ft, average='macro',    zero_division=0)
            f1_wr_m = f1_score(y_true, y_wr, average='macro',    zero_division=0)

            st.divider()
            st.markdown("### 📊 Kết quả so sánh")
            st.caption(f"Đo trên {n_cmp5} comment có nhãn thủ công (manual ground truth)")

            col_h1, col_h2 = st.columns(2)
            with col_h1:
                st.markdown("#### 🟦 Wonrax (general Vietnamese)")
                ka, kb, kc = st.columns(3)
                ka.metric("Accuracy",    f"{acc_wr:.2%}")
                kb.metric("F1-Weighted", f"{f1_wr_w:.4f}")
                kc.metric("F1-Macro",    f"{f1_wr_m:.4f}")
                st.caption(f"Avg confidence: {sum(conf_wr)/len(conf_wr):.0%}")

            with col_h2:
                st.markdown("#### 🟩 PhoBERT Fine-tuned (TVU)")
                ka2, kb2, kc2 = st.columns(3)
                delta_acc = acc_ft - acc_wr
                delta_f1m = f1_ft_m - f1_wr_m
                ka2.metric("Accuracy",    f"{acc_ft:.2%}",  f"{delta_acc:+.2%} vs Wonrax")
                kb2.metric("F1-Weighted", f"{f1_ft_w:.4f}")
                kc2.metric("F1-Macro",    f"{f1_ft_m:.4f}", f"{delta_f1m:+.4f} vs Wonrax")
                st.caption(f"Avg confidence: {sum(conf_ft)/len(conf_ft):.0%}")

            st.divider()

            # Classification reports cạnh nhau
            col_r1, col_r2 = st.columns(2)
            _label_order = ['positive', 'neutral', 'negative']
            with col_r1:
                st.markdown("**Wonrax — Classification Report:**")
                rpt_wr = classification_report(
                    y_true, y_wr,
                    labels=_label_order,
                    target_names=_label_order,
                    zero_division=0
                )
                st.code(rpt_wr)
            with col_r2:
                st.markdown("**Fine-tuned — Classification Report:**")
                rpt_ft = classification_report(
                    y_true, y_ft,
                    labels=_label_order,
                    target_names=_label_order,
                    zero_division=0
                )
                st.code(rpt_ft)

            st.divider()

            # Confusion matrices cạnh nhau
            col_cm1, col_cm2 = st.columns(2)
            _lo = ['positive', 'neutral', 'negative']

            def _make_cm_fig(y_t, y_p, title):
                cm = confusion_matrix(y_t, y_p, labels=_lo)
                cm_n = cm.astype(float) / cm.sum(axis=1, keepdims=True)
                return go.Figure(data=go.Heatmap(
                    z=cm_n,
                    x=[f"Pred {l}" for l in _lo],
                    y=[f"True {l}" for l in _lo],
                    colorscale='RdYlGn',
                    zmin=0, zmax=1,
                    text=[[f"{cm[i][j]}<br>({cm_n[i][j]:.0%})" for j in range(3)] for i in range(3)],
                    texttemplate="%{text}",
                )).update_layout(title=title, height=380)

            with col_cm1:
                st.plotly_chart(
                    _make_cm_fig(y_true, y_wr, "Wonrax — Confusion Matrix"),
                    use_container_width=True
                )
            with col_cm2:
                st.plotly_chart(
                    _make_cm_fig(y_true, y_ft, "Fine-tuned — Confusion Matrix"),
                    use_container_width=True
                )

            st.divider()

            # Bảng những comment 2 model không đồng ý
            df_dis = pd.DataFrame({
                'text':     [c.get('text', '') for c in comments
                             if str(c.get('method','')).lower()=='manual'
                             and str(c.get('sentiment','')).lower() in VALID_SENTIMENTS][:n_cmp5],
                'true':     y_true,
                'wonrax':   y_wr,
                'finetune': y_ft,
            })
            df_dis['wr_ok'] = df_dis['true'] == df_dis['wonrax']
            df_dis['ft_ok'] = df_dis['true'] == df_dis['finetune']

            only_wr_wrong  = df_dis[ df_dis['wr_ok'] & ~df_dis['ft_ok']]
            only_ft_wrong  = df_dis[~df_dis['wr_ok'] &  df_dis['ft_ok']]
            both_wrong     = df_dis[~df_dis['wr_ok'] & ~df_dis['ft_ok']]

            st.markdown("#### 🔍 Phân tích sai lệch")
            d1, d2, d3 = st.columns(3)
            d1.metric("Fine-tuned sai, Wonrax đúng", len(only_wr_wrong))
            d2.metric("Wonrax sai, Fine-tuned đúng",  len(only_ft_wrong))
            d3.metric("Cả hai đều sai",                len(both_wrong))

            with st.expander(f"Xem {len(only_ft_wrong)} comment Wonrax sai nhưng Fine-tuned đúng"):
                if not only_ft_wrong.empty:
                    st.dataframe(
                        only_ft_wrong[['text','true','wonrax','finetune']]
                        .rename(columns={'text':'Nội dung','true':'Nhãn thực',
                                         'wonrax':'Wonrax','finetune':'Fine-tuned'})
                        .head(30),
                        use_container_width=True, hide_index=True
                    )

            with st.expander(f"Xem {len(only_wr_wrong)} comment Fine-tuned sai nhưng Wonrax đúng"):
                if not only_wr_wrong.empty:
                    st.dataframe(
                        only_wr_wrong[['text','true','wonrax','finetune']]
                        .rename(columns={'text':'Nội dung','true':'Nhãn thực',
                                         'wonrax':'Wonrax','finetune':'Fine-tuned'})
                        .head(30),
                        use_container_width=True, hide_index=True
                    )


# ============================================================================
# MAIN
# ============================================================================
def main():
    page = sidebar()
    merged_exists_before_load = MERGED_FILE.exists()
    merged_mtime = MERGED_FILE.stat().st_mtime_ns if merged_exists_before_load else None
    videos, comments, metadata, user = _get_runtime_data(load_data(merged_mtime))

    if not comments:
        with st.sidebar:
            st.divider()
            st.markdown("### Nap du lieu cho Cloud")
            st.caption("Upload file merged JSON, tong_hop_comment.json, hoac CSV comment de chay tam thoi.")
            uploaded_dataset = st.file_uploader(
                "Chon file du lieu",
                type=["json", "csv"],
                key="runtime_dataset_uploader",
            )
            if uploaded_dataset is not None:
                try:
                    parsed_data = _parse_uploaded_dataset(uploaded_dataset)
                    st.session_state["uploaded_runtime_data"] = parsed_data
                    st.success("Da nap du lieu upload vao phien lam viec hien tai.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Khong doc duoc du lieu upload: {e}")

    if (not merged_exists_before_load) and (not comments):
        st.warning(
            f"Khong tim thay du lieu merged: {MERGED_FILE} va fallback {COMMENT_FILE}.")
    elif (not merged_exists_before_load) and comments:
        st.info(
            f"Dang dung fallback tu {COMMENT_FILE} do file merged chua co tren cloud."
        )

    if page == "Tổng quan":
        page_overview(videos, comments, metadata, user)
    elif page == "Sentiment theo Video":
        page_video_sentiment(videos, comments)
    elif page == "Chi tiết bình luận":
        page_comment_detail(videos, comments)
    elif page == "Gán nhãn thủ công":
        page_manual_labeling(videos, comments)
    elif page == "Xuất / Nhập Excel":
        page_export_import(videos, comments)
    elif page == "Đánh giá Gemini":
        page_gemini_evaluation(comments)
    elif page == "Phân tích Chủ đề & Viral":
        page_topic_analysis(videos, comments)
    elif page == "Tiền xử lý Text":
        page_text_preprocessing(comments)
    elif page == "PhoBERT Fine-tuned":
        page_phobert(comments)


if __name__ == "__main__":
    main()
