# 📁 Project Structure - Cleaned & Organized

## ✅ Sau khi Cleanup (Đã xóa 19+ files trùng lặp)

```
tiktok_analytics/
│
├── 📦 pipeline/                      ⭐ MAIN LOGIC
│   ├── __init__.py
│   ├── data_collector.py            # Stage 1: Thu thập raw data
│   ├── data_cleaner.py              # Stage 2: Lọc + removed data
│   ├── data_labeler.py              # Stage 3: Gán nhãn sentiment
│   ├── data_validator.py            # Stage 4: Quality check
│   ├── data_exporter.py             # Stage 5: Export multi-format
│   ├── pipeline_orchestrator.py     # Main orchestrator
│   └── README.md                    # Full documentation
│
├── 🎯 run_pipeline.py                ⭐ ENTRY POINT
│
├── 🧩 modules/                       # Support modules
│   ├── sentiment_analyzer.py        # Sentiment analysis (PhoBERT/underthesea)
│   ├── metrics_analyzer.py          # Engagement metrics
│   ├── tiktok_scraper.py            # TikTok scraper (reference)
│   ├── tiktok_api_scraper.py        # TikTok API scraper
│   ├── youtube_scraper.py           # YouTube scraper (reference)
│   └── __init__.py
│
├── 🛠️ utils/                         # Utilities
│   ├── cache_manager.py             # Caching
│   ├── cleaner.py                   # Data cleaning helpers
│   ├── file_manager.py              # File operations
│   ├── index_manager.py             # Index management
│   ├── logger.py                    # Logging
│   └── __init__.py
│
├── 📊 data/                          # Data storage
│   ├── raw/                         # Stage 1 output
│   ├── cleaned/                     # Stage 2 output
│   ├── removed/                     # Stage 2 removed data
│   ├── labeled/                     # Stage 3 output
│   ├── validated/                   # Stage 4 output
│   ├── reports/                     # Reports
│   └── export/                      # Stage 5 exports
│
├── 📄 reports/                       # Generated reports
│
├── 🗄️ database/                      # Database models (if needed)
│   └── models.py
│
├── 🧪 tests/                         # Tests
│   ├── test_modules.py
│   └── test_integration.py
│
├── 📚 archived/                      # Old backups
│   ├── 2026-03-05_cleanup/
│   └── 2026-03-05_youtube_cleanup/
│
├── ⚙️ config.py                      # Configuration
├── 📦 requirements.txt               # Dependencies
├── 🔒 .env                           # Secrets (not in git)
├── 📖 README.md                      # Main documentation
├── 🚀 QUICK_START_PIPELINE.md        # Quick start guide
└── 🙈 .gitignore

```

---

## 🗑️ Files Đã Xóa (19 files)

### Legacy Scripts (Thay bằng Pipeline):
- ❌ analyze_tiktok.py
- ❌ analyze_tiktok_comprehensive.py
- ❌ main.py (old entry point)
- ❌ create_excel_report.py
- ❌ export_by_sentiment.py
- ❌ visualize_sentiment.py
- ❌ get_more_videos.py
- ❌ cleanup_project.py
- ❌ clean_unused_files.py
- ❌ cleanup_report_20260305_092745.txt
- ❌ apify_config_profile.json

### Advanced Modules (Không cần):
- ❌ modules/audience_analyzer.py
- ❌ modules/comprehensive_analyzer.py
- ❌ modules/performance_predictor.py

### Old Documentation:
- ❌ DASHBOARD_REMOVAL_REPORT.md
- ❌ ORGANIZATION_GUIDE.md
- ❌ PROJECT_STRUCTURE.md (old)
- ❌ NAMING_CONVENTION.md
- ❌ USAGE_GUIDE.md
- ❌ QUICK_START.md (old)

---

## 🎯 Main Entry Points

### 1. Run Pipeline (Recommended) ⭐
```bash
python run_pipeline.py --platform tiktok --id travinhuniversity --videos 30
```

### 2. Python Code
```python
from pipeline import DataPipeline

pipeline = DataPipeline()
results = pipeline.run('tiktok', 'travinhuniversity', max_videos=30)
```

---

## 📊 Data Flow

```
┌─────────────┐
│   Collect   │ → data/raw/*.json
└──────┬──────┘
       ↓
┌─────────────┐
│    Clean    │ → data/cleaned/*.json + data/removed/*.json
└──────┬──────┘
       ↓
┌─────────────┐
│    Label    │ → data/labeled/*.json
└──────┬──────┘
       ↓
┌─────────────┐
│  Validate   │ → data/validated/*.json + reports/*.txt
└──────┬──────┘
       ↓
┌─────────────┐
│   Export    │ → data/export/*.{json,csv,xlsx,parquet}
└─────────────┘
```

---

## 📚 Documentation

- **QUICK_START_PIPELINE.md** - Quick start guide
- **README.md** - Main documentation  
- **pipeline/README.md** - Full pipeline documentation with code explanations

---

## 🚀 Quick Commands

```bash
# Run pipeline
python run_pipeline.py --platform tiktok --id user123 --videos 30

# Run with hybrid labeling
python run_pipeline.py --platform tiktok --id user123 --label hybrid

# Export specific formats
python run_pipeline.py --platform tiktok --id user123 --formats json parquet

# Help
python run_pipeline.py --help
```

---

## 📏 Metrics

**Before Cleanup:**
- Total files: 40+
- Main scripts: 10+
- Documentation: 8+

**After Cleanup:**
- Total files: 20
- Main entry: 1 (run_pipeline.py)
- Documentation: 2 (README.md, QUICK_START_PIPELINE.md)

**Improvement:**
- ✅ 50% fewer files
- ✅ Single source of truth
- ✅ Clear structure
- ✅ Easy to maintain

---

**Last Updated:** 2026-03-06
**Version:** 2.0 (Post-cleanup)
**Status:** ✅ Production Ready & Organized
