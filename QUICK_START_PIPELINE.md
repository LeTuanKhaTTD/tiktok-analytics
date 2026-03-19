# 🚀 Quick Start - Data Pipeline

## ✅ Đã Tạo Gì?

Tôi đã xây dựng một **professional data pipeline** theo đúng best practices của các data team thực tế:

```
📦 pipeline/
├── __init__.py                    # Package initialization
├── data_collector.py              # Stage 1: Thu thập raw data
├── data_cleaner.py                # Stage 2: Lọc + lưu removed data
├── data_labeler.py                # Stage 3: Gán nhãn (Auto/Manual/Hybrid)
├── data_validator.py              # Stage 4: Quality check
├── data_exporter.py               # Stage 5: Export JSON/CSV/Excel/Parquet
├── pipeline_orchestrator.py       # Main orchestrator
└── README.md                      # Full documentation

📄 run_pipeline.py                  # CLI entry point
```

---

## 🎯 Pipeline Flow

```
RAW DATA → CLEANED → LABELED → VALIDATED → EXPORTED
   ↓          ↓         ↓          ↓           ↓
Stage 1    Stage 2   Stage 3    Stage 4     Stage 5
Collect    Clean     Label      Validate    Export
```

###  Stage 1: Data Collector ✅  
**Nhiệm vụ:** Thu thập raw data từ API

**Output:** `data/raw/tiktok_user_timestamp_raw.json`

**Vibe Concept:** **LUÔN LƯU RAW DATA!**
- Có thể trace back về nguồn
- Re-run pipeline với rules khác
- Debug khi có vấn đề

```python
from pipeline import DataCollector

collector = DataCollector()
result = collector.collect_and_save('tiktok', 'travinhuniversity', 30)
```

---

### Stage 2: Data Cleaner ✅
**Nhiệm vụ:** Lọc spam, duplicate, normalize format

**Outputs:**
- `data/cleaned/tiktok_user_timestamp_cleaned.json`
- `data/removed/tiktok_user_timestamp_removed.json` ← **QUAN TRỌNG!**

**Vibe Concept:** **LƯU CẢ DATA BỊ LOẠI!**
- Review false positives
- Tune cleaning rules
- Audit trail

```python
from pipeline import DataCleaner

cleaner = DataCleaner()
result = cleaner.clean_data(raw_data)
paths = cleaner.save_cleaned_data(
    result['cleaned_data'],
    result['removed_data'],
    'tiktok',
    'travinhuniversity'
)
```

---

### Stage 3: Data Labeler ✅
**Nhiệm vụ:** Gán nhãn sentiment

**3 Modes:**

1. **AUTO** - ML model tự động
   - ✅ Nhanh, scale tốt
   - ⚠️ Accuracy ~70-85%

2. **MANUAL** - Human labeling
   - ✅ Accuracy ~95-99%
   - ⚠️ Chậm, không scale

3. **HYBRID** - Auto + manual review ⭐ **RECOMMENDED**
   - ✅ Cân bằng speed vs accuracy
   - Low confidence → Human review

**Vibe Concept:** **CONFIDENCE THRESHOLD!**
```python
# confidence >= 0.7 → Accept
# confidence < 0.7 → Human review
```

```python
from pipeline import DataLabeler, LabelMethod

labeler = DataLabeler(confidence_threshold=0.7)
result = labeler.label_data(cleaned_data, method=LabelMethod.AUTO)
```

---

### Stage 4: Data Validator ✅
**Nhiệm vụ:** Quality check và validation

**Validation Rules:**
1. ✓ Completeness - Có đủ fields không?
2. ✓ Consistency - Data nhất quán không?
3. ✓ Quality - Confidence scores OK không?
4. ✓ Distribution - Sentiment reasonable không?

**Severity Levels:**
- 🔴 ERROR - Critical, phải fix
- 🟡 WARNING - Nên review
- 🔵 INFO - FYI, tracking

```python
from pipeline import DataValidator

validator = DataValidator(min_confidence=0.6)
result = validator.validate_data(labeled_data)

if result['passed']:
    print("✅ Validation passed!")
else:
    print(f"❌ {result['stats']['error_count']} errors found")
```

---

### Stage 5: Data Exporter ✅
**Nhiệm vụ:** Export ra nhiều formats

**Formats:**
| Format | Size | Speed | Use Case |
|--------|------|-------|----------|
| JSON | Medium | Fast | APIs, web apps |
| CSV | Medium | Fast | Excel, analysis |
| Excel | Large | Medium | Business reports |
| **Parquet** | **Small** | **Fastest** | **Production!** ⭐ |

**Why Parquet?**
- 10-100x smaller than CSV
- 10-100x faster reads
- Perfect cho BigQuery, Spark, data warehouse

```python
from pipeline import DataExporter

exporter = DataExporter()
files = exporter.export_all(
    validated_data,
    'tiktok',
    'travinhuniversity',
    formats=['json', 'csv', 'excel', 'parquet']
)
```

---

## 💻 Cách Sử Dụng

### Method 1: CLI (Recommended)

```bash
# Basic usage
python run_pipeline.py --platform tiktok --id travinhuniversity --videos 30

# With hybrid labeling
python run_pipeline.py --platform tiktok --id user123 --label hybrid

# Export specific formats
python run_pipeline.py --platform tiktok --id user123 --formats json parquet
```

### Method 2: Python Code

```python
from pipeline import DataPipeline

# Initialize
pipeline = DataPipeline(
    data_dir="data",
    confidence_threshold=0.7,
    use_vietnamese=True
)

# Run full pipeline
results = pipeline.run(
    platform="tiktok",
    identifier="travinhuniversity",
    max_videos=30,
    labeling_method="auto",
    export_formats=['json', 'csv', 'excel', 'parquet']
)

# Check results
if results["success"]:
    print(f"✅ Success! Duration: {results['duration_seconds']:.1f}s")
    print(f"Exported: {results['results']['export']['files']}")
else:
    print(f"❌ Failed: {results['error']}")
```

---

## 🔥 Code Quan Trọng - VIBE CODING PHẢI BIẾT

### 1. Metadata Tracking ⭐

**Location:** `data_collector.py`

```python
def _create_metadata(self, platform, identifier):
    return {
        "platform": platform,
        "identifier": identifier,
        "collected_at": datetime.now().isoformat(),
        "collector_version": "1.0.0",
        "data_schema_version": "1.0"
    }
```

**Vibe:** Metadata = Data Lineage
- Biết data từ đâu, lúc nào
- Version để handle schema changes
- **Critical cho production!**

---

### 2. Validation Pattern với Reason ⭐

**Location:** `data_cleaner.py`

```python
def _validate_comment(self, comment):
    # Check empty
    if not comment.get('text'):
        return False, "empty_text"  # ← Return reason!
    
    # Check length
    if len(comment['text']) < 2:
        return False, f"too_short_{len(comment['text'])}"
    
    return True, ""
```

**Vibe:** Return reason khi fail
- Debug dễ: Biết tại sao reject
- Generate reports: Count reasons
- Tune rules: Biết rule nào trigger nhiều

**Pattern:** `(is_valid: bool, reason: str)`

---

### 3. Confidence Threshold Strategy ⭐⭐⭐

**Location:** `data_labeler.py`

```python
# High confidence → Accept
if confidence >= self.confidence_threshold:
    labeled.append(comment)
# Low confidence → Human review
else:
    low_confidence.append(comment)
```

** Vibe:** Confidence = Model uncertainty

**Tune theo use case:**
```python
# Critical (medical, legal)
confidence_threshold = 0.9  # Very strict

# Production (social media)
confidence_threshold = 0.7  # Balanced ⭐

# Prototyping
confidence_threshold = 0.5  # Loose
```

---

### 4. Validation với Severity Levels ⭐

**Location:** `data_validator.py`

```python
class ValidationIssue:
    def __init__(self, severity, rule, message):
        self.severity = severity  # ERROR, WARNING, INFO
        self.rule = rule
        self.message = message
```

**Vibe:** Không phải tất cả issues đều critical
- **ERROR** → Block pipeline
- **WARNING** → Continue nhưng review
- **INFO** → FYI, metrics

---

### 5. Pipeline Orchestration Pattern ⭐⭐⭐

**Location:** `pipeline_orchestrator.py`

```python
class DataPipeline:
    def run(self, ...):
        try:
            # Stage 1 → 2 → 3 → 4 → 5
            self._run_stage_collect(...)
            self._run_stage_clean(...)
            self._run_stage_label(...)
            self._run_stage_validate(...)
            self._run_stage_export(...)
            
            return {"success": True, ...}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

**Vibe:** Pipeline = Chain of Responsibility
- Mỗi stage nhận input từ stage trước
- Error handling graceful
- **Separation of concerns**

---

### 6. Export Format Selection ⭐⭐

**Location:** `data_exporter.py`

```python
# JSON - Universal
json.dump(data, f, ensure_ascii=False, indent=2)

# CSV - Flat structure
writer.writerow(['id', 'text', 'sentiment'])

# Excel - Multiple sheets
with pd.ExcelWriter(path) as writer:
    df1.to_excel(writer, sheet_name='Comments')
    df2.to_excel(writer, sheet_name='Summary')

# Parquet - Columnar, compressed ⭐
df.to_parquet(path, compression='snappy')
```

**Vibe:** Format selection matters!

**Use Parquet when:**
- Large datasets (>100MB)
- Speed is critical
- Data warehouse integration
- **Production recommendation!**

---

## 📊 Output Structure

```
data/
├── raw/                          # Stage 1
│   └── tiktok_user_20260306_120000_raw.json
├── cleaned/                      # Stage 2
│   └── tiktok_user_20260306_120000_cleaned.json
├── removed/                      # Stage 2 (removed data)
│   └── tiktok_user_20260306_120000_removed.json
├── labeled/                      # Stage 3
│   └── tiktok_user_20260306_120000_labeled.json
├── validated/                    # Stage 4
│   └── tiktok_user_20260306_120000_validated.json
├── reports/                      # Reports
│   ├── cleaning_report.txt
│   └── validation_report.txt
└── export/                       # Stage 5
    ├── tiktok_user_20260306_120000_export.json
    ├── tiktok_user_20260306_120000_comments.csv
    ├── tiktok_user_20260306_120000_export.xlsx
    └── tiktok_user_20260306_120000_comments.parquet
```

---

## 🎓 Key Takeaways - VIBE ESSENTIALS

1. **Separation of Concerns** → Mỗi stage một nhiệm vụ
2. **Data Lineage** → Track data từ nguồn đến kết quả
3. **Graceful Degradation** → Handle errors không crash
4. **Confidence Thresholds** → Biết khi nào cần human review
5. **Validation ≠ Testing** → Test code, validate data
6. **Multiple Exports** → Users chọn format phù hợp
7. **Save Everything** → Raw, cleaned, removed, reports
8. **Metadata Matters** → Version, timestamp, source
9. **Parquet for Production** → Fast, compressed, type-safe
10. **Pipeline Pattern** → Chain of responsibility, resumable

---

## 🔧 Troubleshooting

### Import Error
```bash
# Error: cannot import name 'DataPipeline'
# Fix: Ensure you're in the correct directory
cd tiktok_analytics
python run_pipeline.py --help
```

### Dependencies
```bash
# Install required packages
pip install pandas openpyxl pyarrow
```

### Test Pipeline
```bash
# Quick test with minimal data
python run_pipeline.py --platform tiktok --id test --videos 5 --formats json
```

---

## 📚 Further Reading

- Full documentation: `pipeline/README.md`
- Code examples: Each `.py` file has detailed comments
- Best practices: Search for "Vibe:" comments in code

---

**Created:** 2026-03-06  
**Version:** 1.0.0  
**Pipeline Status:** ✅ Production Ready

**Chúc bạn code vui vẻ! 🚀**
