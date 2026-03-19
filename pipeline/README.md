# Data Pipeline - Professional Edition 🚀

Pipeline xử lý dữ liệu chuyên nghiệp cho TikTok/YouTube Analytics, được thiết kế theo best practices của các data team thực tế.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Pipeline Architecture](#pipeline-architecture)
3. [Code Quan Trọng - Vibe Coding Phải Biết](#code-quan-trọng---vibe-coding-phải-biết)
4. [Usage](#usage)
5. [Best Practices](#best-practices)

---

## 🎯 Overview

Pipeline gồm 5 stages tuần tự:

```
Raw Data → Cleaned Data → Labeled Data → Validated Data → Exported Files
   ↓            ↓              ↓              ↓                ↓
Stage 1      Stage 2        Stage 3        Stage 4         Stage 5
Collect      Clean          Label          Validate        Export
```

### Tại sao cần Pipeline?

**❌ Bad Practice (Không có pipeline):**
```python
# Code mess, không maintainable
data = scrape_tiktok()
clean_data = [x for x in data if x['text']]  # Inline logic
for item in clean_data:
    item['sentiment'] = predict(item['text'])  # Không track được
save_json(clean_data)  # Mất data gốc, không trace được
```

**✅ Good Practice (Có pipeline):**
```python
pipeline = DataPipeline()
results = pipeline.run(platform='tiktok', identifier='user123')
# ✓ Có raw data backup
# ✓ Track được removed data
# ✓ Có validation reports
# ✓ Multi-format exports
# ✓ Reproducible
```

---

## 🏗️ Pipeline Architecture

### Stage 1: Data Collector
**Purpose:** Thu thập raw data từ API

```python
from pipeline import DataCollector

collector = DataCollector(output_dir="data/raw")
result = collector.collect_and_save(
    platform="tiktok",
    identifier="travinhuniversity",
    max_videos=30
)
```

**Output:**
- `data/raw/tiktok_travinhuniversity_20260306_120000_raw.json`

**Vibe Concept:** **Luôn lưu raw data!**
- Có thể trace back về nguồn
- Re-run pipeline với rules khác
- Debug khi có vấn đề

---

### Stage 2: Data Cleaner
**Purpose:** Lọc spam, duplicate, normalize format

```python
from pipeline import DataCleaner

cleaner = DataCleaner(
    output_cleaned_dir="data/cleaned",
    output_removed_dir="data/removed",
    output_report_dir="data/reports"
)

result = cleaner.clean_data(raw_data)
paths = cleaner.save_cleaned_data(
    cleaned_data=result['cleaned_data'],
    removed_data=result['removed_data'],
    platform='tiktok',
    identifier='travinhuniversity'
)
```

**Outputs:**
- `data/cleaned/tiktok_user_timestamp_cleaned.json`
- `data/removed/tiktok_user_timestamp_removed.json` ← **QUAN TRỌNG!**
- `data/reports/tiktok_user_timestamp_cleaning_report.txt`

**Vibe Concept:** **Lưu cả data bị loại!**
- Review false positives
- Tune cleaning rules
- Audit trail cho compliance

---

### Stage 3: Data Labeler
**Purpose:** Gán nhãn sentiment (Auto/Manual/Hybrid)

```python
from pipeline import DataLabeler, LabelMethod

labeler = DataLabeler(
    output_dir="data/labeled",
    confidence_threshold=0.7,  # Quan trọng!
    use_vietnamese=True
)

result = labeler.label_data(
    cleaned_data,
    method=LabelMethod.AUTO  # hoặc MANUAL, HYBRID
)
```

**3 Methods:**

1. **AUTO** - ML model tự động
   - ✅ Nhanh, scale tốt
   - ⚠️ Accuracy ~70-85%
   - Use case: Large datasets, không yêu cầu accuracy cao

2. **MANUAL** - Human labeling
   - ✅ Accuracy cao nhất ~95-99%
   - ⚠️ Chậm, không scale
   - Use case: Gold standard dataset, critical data

3. **HYBRID** - Auto + manual review
   - ✅ Cân bằng speed vs accuracy
   - Low confidence → Human review
   - Use case: **Production recommended!**

**Vibe Concept:** **Confidence Threshold là key!**
```python
# confidence_threshold = 0.7
# Confidence 0.8 → Accept (auto)
# Confidence 0.6 → Human review (low confidence)
```

---

### Stage 4: Data Validator
**Purpose:** Quality check và validation

```python
from pipeline import DataValidator

validator = DataValidator(
    output_validated_dir="data/validated",
    output_report_dir="data/reports",
    min_confidence=0.6,
    max_neutral_ratio=0.5
)

result = validator.validate_data(labeled_data)
```

**Validation Rules:**

1. **Completeness** - Có đủ fields không?
2. **Consistency** - Data có nhất quán không?
3. **Quality** - Confidence scores OK không?
4. **Distribution** - Sentiment distribution reasonable không?

**Severity Levels:**
- 🔴 **ERROR** - Critical, phải fix
- 🟡 **WARNING** - Nên review
- 🔵 **INFO** - Thông tin tham khảo

**Vibe Concept:** **Validation ≠ Testing**
- Testing: Test code logic
- Validation: Check data quality

---

### Stage 5: Data Exporter
**Purpose:** Export ra nhiều formats

```python
from pipeline import DataExporter

exporter = DataExporter(output_dir="data/export")
exported_files = exporter.export_all(
    validated_data=validated_data,
    platform='tiktok',
    identifier='travinhuniversity',
    formats=['json', 'csv', 'excel', 'parquet']
)
```

**Format Comparison:**

| Format  | Size | Speed | Use Case |
|---------|------|-------|----------|
| JSON    | 📊 Medium | Fast | APIs, web apps, universal |
| CSV     | 📊 Medium | Fast | Excel, simple analysis |
| Excel   | 📊 Large | Medium | Business users, reports |
| Parquet | 📊 Small | **Fastest** | **Big data, analytics, data warehouse** |

**Vibe Concept:** **Parquet cho Production!**
```python
# CSV: 10 MB
# Parquet: 1 MB (10x smaller!)
# Query speed: 10-100x faster
```

Why?
- Columnar storage → Read only needed columns
- Compressed → Save storage costs
- Type-safe → Schema preserved
- Perfect cho Spark, BigQuery, Snowflake

---

## 🔥 Code Quan Trọng - Vibe Coding Phải Biết

### 1. Retry Logic với Exponential Backoff

**Location:** `data_collector.py`

```python
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def _create_session(self):
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,  # Retry 3 lần
        status_forcelist=[429, 500, 502, 503, 504],  # Retry những status codes này
        allowed_methods=["HEAD", "GET", "POST"],
        backoff_factor=1  # Wait: 1s, 2s, 4s
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session
```

**Vibe:** API calls thường fail (network issues, rate limits)
- Tự động retry với exponential backoff
- 429 = Rate limit → Đợi rồi retry
- 500, 502, 503, 504 = Server errors → Retry
- **Không retry 4xx errors khác** (bad request, không có ý nghĩa retry)

---

### 2. Metadata Tracking

**Location:** `data_collector.py`

```python
def _create_metadata(self, platform: str, identifier: str):
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
- Tool info để debug
- **Critical cho production systems!**

---

### 3. Validation Patterns

**Location:** `data_cleaner.py`

```python
def _validate_comment(self, comment: Dict[str, Any]) -> Tuple[bool, str]:
    # Check required fields
    if not comment.get('id'):
        return False, "missing_id"
    
    text = comment.get('text', '').strip()
    
    # Check empty
    if not text:
        return False, "empty_text"
    
    # Check length
    if len(text) < self.min_text_length:
        return False, f"too_short_{len(text)}"
    
    # Check spam
    for keyword in self.spam_keywords:
        if keyword.lower() in text.lower():
            return False, f"spam_keyword_{keyword}"
    
    return True, ""
```

**Vibe:** Return reason khi fail
- Debug dễ dàng: Biết tại sao data bị reject
- Generate reports: Count removal reasons
- Tune rules: Biết rule nào trigger nhiều nhất
- Pattern: `(is_valid: bool, reason: str)`

---

### 4. Confidence Score Strategy

**Location:** `data_labeler.py`

```python
# High confidence → Accept
if confidence >= self.confidence_threshold:
    labeled.append(comment)
# Low confidence → Human review
else:
    low_confidence.append(comment)
```

**Vibe:** Confidence = Model uncertainty
- HIGH (>0.8): Model rất chắc → Accept
- MEDIUM (0.6-0.8): OK → Accept hoặc review tùy threshold
- LOW (<0.6): Model không chắc → **Phải review!**

**Tune threshold theo use case:**
```python
# Critical application (medical, legal)
confidence_threshold = 0.9  # Very strict

# Production application (social media analysis)
confidence_threshold = 0.7  # Balanced

# Prototyping
confidence_threshold = 0.5  # Loose
```

---

### 5. Validation với Severity Levels

**Location:** `data_validator.py`

```python
class ValidationIssue:
    def __init__(self, severity: ValidationSeverity, 
                 rule: str, message: str, count: int = 1):
        self.severity = severity  # ERROR, WARNING, INFO
        self.rule = rule
        self.message = message
        self.count = count
```

**Vibe:** Không phải tất cả issues đều critical
- **ERROR** → Block pipeline, phải fix
- **WARNING** → Continue nhưng cần review
- **INFO** → FYI, tracking metrics

Example:
```python
# Missing data = ERROR
ValidationIssue(ValidationSeverity.ERROR, 
                "missing_sentiment", 
                "10 comments missing labels")

# Low confidence = WARNING
ValidationIssue(ValidationSeverity.WARNING,
                "low_confidence",
                "30% comments have confidence <0.6")

# Stats = INFO
ValidationIssue(ValidationSeverity.INFO,
                "sentiment_stats",
                "Distribution: 40% pos, 30% neg, 30% neutral")
```

---

### 6. Pipeline Orchestration Pattern

**Location:** `pipeline_orchestrator.py`

```python
class DataPipeline:
    def run(self, platform, identifier, max_videos):
        try:
            # Stage 1
            self._run_stage_collect(platform, identifier, max_videos)
            
            # Stage 2 - Uses output từ Stage 1
            self._run_stage_clean(platform, identifier)
            
            # Stage 3 - Uses output từ Stage 2
            self._run_stage_label(platform, identifier, method)
            
            # ... continue chain
            
        except Exception as e:
            # Handle errors gracefully
            return {"success": False, "error": str(e)}
```

**Vibe:** Pipeline = Chain of Responsibility
- Mỗi stage nhận input từ stage trước
- Error ở stage nào → Stop và report
- Có thể resume từ stage bị failed
- **Separation of concerns** → Mỗi stage một trách nhiệm

---

### 7. Export Format Selection

**Location:** `data_exporter.py`

```python
# JSON - Universal
with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# CSV - Excel-friendly
with open(filepath, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'text', 'sentiment'])
    writer.writerows(rows)

# Excel - Multiple sheets
with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
    summary_df.to_excel(writer, sheet_name='Summary')
    comments_df.to_excel(writer, sheet_name='Comments')

# Parquet - Big data
df.to_parquet(filepath, compression='snappy', index=False)
```

**Vibe:** Format selection matters!

**Use JSON when:**
- API responses
- Config files
- Web applications
- Need nested structure

**Use CSV when:**
- Simple tabular data
- Excel import/export
- Quick analysis
- Human-readable

**Use Excel when:**
- Business reports
- Multiple related tables (sheets)
- Non-technical users
- Need formatting/charts

**Use Parquet when:**
- Large datasets (>100MB)
- Analytics/data warehouse
- Speed is critical
- Integration với Spark/BigQuery
- **Production recommendation!**

---

## 🚀 Usage

### Basic Usage

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
    print(f"✅ Completed in {results['duration_seconds']:.1f}s")
    print(f"Exported files: {results['results']['export']['files']}")
else:
    print(f"❌ Failed: {results['error']}")
```

### Command Line

```bash
# TikTok analysis
python run_pipeline.py --platform tiktok --id travinhuniversity --videos 30

# YouTube analysis với hybrid labeling
python run_pipeline.py --platform youtube --id UCaxnllxL894OHbc_6VQcGmA --label hybrid

# Export specific formats only
python run_pipeline.py --platform tiktok --id user123 --formats json parquet
```

### Individual Stages

```python
# Run chỉ một stage riêng lẻ

# Stage 1: Collect
from pipeline import DataCollector
collector = DataCollector()
result = collector.collect_and_save('tiktok', 'user123', 30)

# Stage 2: Clean
from pipeline import DataCleaner
cleaner = DataCleaner()
result = cleaner.clean_data(raw_data)

# Stage 3: Label
from pipeline import DataLabeler, LabelMethod
labeler = DataLabeler(confidence_threshold=0.7)
result = labeler.label_data(cleaned_data, method=LabelMethod.HYBRID)

# Stage 4: Validate
from pipeline import DataValidator
validator = DataValidator(min_confidence=0.6)
result = validator.validate_data(labeled_data)

# Stage 5: Export
from pipeline import DataExporter
exporter = DataExporter()
files = exporter.export_all(validated_data, 'tiktok', 'user123')
```

---

## 💡 Best Practices

### 1. Always Save Raw Data
```python
# ❌ Bad - Mất data gốc
data = scrape_api()
cleaned = clean(data)  # Raw data bị mất!
save(cleaned)

# ✅ Good - Có thể trace back
collector.collect_and_save()  # Lưu raw
cleaner.clean_data()  # Lưu cleaned + removed
```

### 2. Track Removal Reasons
```python
# ✅ Good - Biết tại sao data bị remove
comment['removal_reason'] = 'spam_keyword_http://'
removed_comments.append(comment)

# Generate report để review
removal_stats = Counter(c['removal_reason'] for c in removed)
```

### 3. Use Confidence Thresholds
```python
# ✅ Good - Separate high vs low confidence
if confidence >= 0.7:
    auto_labeled.append(comment)
else:
    needs_review.append(comment)  # Human review
```

### 4. Validate Before Use
```python
# ✅ Good - Always validate
validator = DataValidator()
result = validator.validate_data(labeled_data)

if result['passed']:
    export_data(result['validated_data'])
else:
    print(f"⚠️ Validation failed: {result['stats']['error_count']} errors")
    # Review validation report
```

### 5. Export Multiple Formats
```python
# ✅ Good - Users chọn format phù hợp
exporter.export_all(
    data,
    formats=['json', 'csv', 'excel', 'parquet']
)

# Business users → Excel
# Developers → JSON
# Data analysts → Parquet
```

### 6. Handle Errors Gracefully
```python
# ✅ Good - Try-catch và log errors
try:
    result = pipeline.run(...)
except Exception as e:
    logger.error(f"Pipeline failed: {e}")
    send_alert(e)  # Alert team
    return {"success": False, "error": str(e)}
```

### 7. Log Everything
```python
# ✅ Good - Track progress
print(f"✅ Stage 1 completed: {len(videos)} videos collected")
print(f"✅ Stage 2 completed: {kept} kept, {removed} removed")
print(f"⚠️  Stage 3 warning: {low_conf_count} need review")
```

---

## 📊 Output Structure

```
data/
├── raw/                          # Stage 1 output
│   └── tiktok_user_20260306_120000_raw.json
├── cleaned/                      # Stage 2 output
│   └── tiktok_user_20260306_120000_cleaned.json
├── removed/                      # Stage 2 removed data
│   └── tiktok_user_20260306_120000_removed.json
├── labeled/                      # Stage 3 output
│   └── tiktok_user_20260306_120000_labeled.json
├── validated/                    # Stage 4 output
│   └── tiktok_user_20260306_120000_validated.json
├── reports/                      # Reports từ các stages
│   ├── tiktok_user_20260306_120000_cleaning_report.txt
│   └── tiktok_user_20260306_120000_validation_report.txt
└── export/                       # Stage 5 exports
    ├── tiktok_user_20260306_120000_export.json
    ├── tiktok_user_20260306_120000_videos.csv
    ├── tiktok_user_20260306_120000_comments.csv
    ├── tiktok_user_20260306_120000_export.xlsx
    ├── tiktok_user_20260306_120000_videos.parquet
    └── tiktok_user_20260306_120000_comments.parquet
```

---

## 🎓 Key Takeaways - Vibe Coding Essentials

1. **Separation of Concerns** → Mỗi stage một nhiệm vụ rõ ràng
2. **Data Lineage** → Track data từ nguồn đến kết quả
3. **Graceful Degradation** → Handle errors không crash
4. **Confidence Thresholds** → Biết khi nào cần human review
5. **Validation ≠ Testing** → Test code, validate data
6. **Multiple Exports** → Users chọn format phù hợp
7. **Save Everything** → Raw, cleaned, removed, reports
8. **Metadata Matters** → Version, timestamp, source
9. **Retry Logic** → Network fails, handle gracefully
10. **Parquet for Production** → Fast, compressed, type-safe

---

## 📚 Further Reading

- [Apache Parquet Documentation](https://parquet.apache.org/)
- [Data Pipeline Design Patterns](https://www.oreilly.com/library/view/data-pipelines-pocket/9781492087823/)
- [ML Confidence Calibration](https://scikit-learn.org/stable/modules/calibration.html)
- [Data Validation Strategies](https://www.tensorflow.org/tfx/guide/tfdv)

---

**Created:** 2026-03-06  
**Version:** 1.0.0  
**Author:** Data Pipeline Team
