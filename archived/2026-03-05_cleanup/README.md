# 🗑️ Archived Files - Cleanup 2026-03-05

## Lý do archive

Các files này đã được di chuyển vào archived vì:
- Là utility scripts dùng 1 lần để xử lý data
- Trùng chức năng với modules mới
- Backup files không cần thiết

## Files đã archive (13 files)

### Nhóm 1: Utility Scripts (8 files)
1. `clean_non_vietnamese.py` - Lọc comments không phải tiếng Việt
2. `filter_apify_data.py` - Lọc data từ Apify
3. `find_french.py` - Tìm comments tiếng Pháp
4. `remove_french.py` - Xóa comments tiếng Pháp
5. `organize_comments.py` - Sắp xếp comments
6. `check_tiktok_data.py` - Kiểm tra data
7. `analyze_apify_data.py` - Phân tích data Apify
8. `export_by_sentiment.py` - Xuất theo sentiment

**Thay thế bằng:** Các modules trong `modules/` và utils trong `utils/`

### Nhóm 2: Files Trùng Chức Năng (4 files)
1. `run_sentiment_analysis.py` - Trùng với `modules/sentiment_analyzer.py`
2. `run_sentiment_analysis_phobert.py` - Trùng với sentiment analyzer
3. `visualize_sentiment.py` - Đã có `dashboard_app.py` (mới & tốt hơn)
4. `create_excel_report.py` - Dashboard có thể export

**Thay thế bằng:** 
- Sentiment: `modules/sentiment_analyzer.py`
- Visualization: `dashboard_app.py` (Streamlit)
- Reports: `api_server.py` endpoints

### Nhóm 3: File Backup (1 file)
1. `apify_raw_data_backup.json` (1.07 MB) - Raw data backup không cần

**Lưu ý:** Data thật nằm trong `data/` folder

## Tổng kết

- **Tổng files:** 13
- **Tổng dung lượng:** ~1.12 MB
- **Dòng code tiết kiệm:** ~2,054 dòng
- **Trạng thái:** ✅ An toàn để xóa sau 30 ngày

## Khôi phục

Nếu cần khôi phục file nào:
```bash
cd d:\Thuc_tap\tiktok_analytics
Move-Item "archived\2026-03-05_cleanup\[tên_file]" .
```

## Xóa vĩnh viễn

Sau 30 ngày (05/04/2026), nếu không cần:
```bash
Remove-Item -Recurse -Force "archived\2026-03-05_cleanup"
```

---

**Archived Date:** March 5, 2026
**Archived By:** AI Assistant
**Reason:** Dự án cleanup để gọn gàng hơn
