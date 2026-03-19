# TikTok Analytics with PhoBERT Sentiment Model 🎬

Hệ thống phân tích dữ liệu TikTok với mô hình PhoBERT tinh chỉnh để phân tích cảm xúc (sentiment) từ comments tiếng Việt. Dự án bao gồm thu thập dữ liệu, xử lý, đánh dấu nhãn (labeling), đào tạo mô hình ML, và dashboard trực quan hóa.

## ✨ Tính năng chính

### 📊 Thu thập dữ liệu
- Thu thập thông tin TikTok từ nhiều nguồn:
  - **TikTok API Scraper**: Sử dụng URL crawler
  - **Apify**: Thu thập từ Apify Actor
  - **YouTube**: Dữ liệu YouTube tương ứng
- Lưu trữ thông tin video, comments, metrics
- Xử lý và làm sạch dữ liệu (data cleaning & validation)

### 😊 Phân tích Sentiment với PhoBERT
- **Mô hình**: `vinai/phobert-base` tinh chỉnh
- **Phân lớp**: 3 lớp (Positive, Neutral, Negative)
- **Độ chính xác**: 
  - Hold-out test: ~72.43% (301 mẫu)
  - Manual benchmark: ~78.29% (2004 mẫu)
- **Dữ liệu huấn luyện**:
  - Manual labeled: 2004 comments
  - Semi-supervised (pseudo-labeled): 778 comments
  - Tổng: 2865 comments

### 📈 Phân tích Metrics
- **Engagement Rate**: (likes + comments) / views × 100%
- **Like Rate, Comment Rate, Share Rate**
- **Interaction Distribution**: Phân phối tương tác
- **Sentiment Distribution**: Phân phối cảm xúc theo video
- **Trend Analysis**: Xu hướng theo thời gian

### 📊 Dashboard Streamlit
- Trực quan hóa metrics theo ngày/video
- Biểu đồ sentiment phân bố
- Filter theo video, ngày, loại metrics
- Xuất báo cáo PDF/PPTX
- Real-time analytics overview

## � Cài đặt & Setup

### Yêu cầu hệ thống
- Python 3.8+
- PyTorch 1.x với hỗ trợ CUDA (GPU khuyến nghị)
- Windows/Linux/MacOS
- RAM tối thiểu 8GB, GPU 4GB+ (VRAM)

### Bước 1: Clone project
```bash
git clone https://github.com/LeTuanKhaTTD/tiktok-analytics.git
cd tiktok-analytics
```

### Bước 2: Tạo môi trường ảo
```bash
python -m venv .venv-2
# Windows
.venv-2\Scripts\activate
# Linux/MacOS
source .venv-2/bin/activate
```

### Bước 3: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Bước 4: Cấu hình (tuỳ chọn)
```bash
# Copy template config
cp .env.example .env

# Chỉnh sửa .env với API keys nếu cần
# YOUTUBE_API_KEY=your_key_here
# TIKTOK_ACCOUNT_ID=your_id
```

## 📖 Sử dụng

### 1️⃣ Chạy Dashboard Streamlit
```bash
streamlit run dashboard.py
```
Truy cập `http://localhost:8501` để xem trực quan hóa dữ liệu real-time.

### 2️⃣ Thu thập dữ liệu TikTok
```bash
# Pipeline tổng quát
python run_pipeline.py --platform tiktok --id travinhuniversity --videos 30

# Pipeline APIFY (nếu có tài khoản Apify)
python run_pipeline_apify.py

# Pipeline Real (crawler trực tiếp)
python run_pipeline_real.py
```

### 3️⃣ Huấn luyện lại mô hình PhoBERT

#### Bước 1: Chuẩn bị dữ liệu
```bash
python prepare_retrain_datasets.py
```
Tạo ra 3 datasets:
- `data/export/retrain_manual_only_2004.json` - Chỉ dữ liệu đã đánh dấu
- `data/export/retrain_manual_phobert_2782.json` - Dữ liệu đã đánh dấu + pseudo-label
- `data/export/retrain_all_labeled_2865.json` - Tất cả dữ liệu đã gán nhãn

#### Bước 2: Chạy Notebook huấn luyện
```bash
jupyter notebook phobert_finetune.ipynb
```

Hoặc trong VS Code, mở notebook và chọn kernel Python từ `.venv-2`

**Các kịch bản huấn luyện** (sửa Cell 12 trong notebook):

```python
# Kịch bản A: Chỉ dữ liệu manual
STRICT_MANUAL_ONLY = True
TRAIN_SOURCES = ['manual']
DATA_PATH = 'data/export/retrain_manual_only_2004.json'

# Kịch bản B: Manual + Pseudo-label
STRICT_MANUAL_ONLY = False
TRAIN_SOURCES = ['manual', 'phobert']
DATA_PATH = 'data/export/retrain_manual_phobert_2782.json'

# Kịch bản C: Tất cả
STRICT_MANUAL_ONLY = False
TRAIN_SOURCES = ['manual', 'phobert']
DATA_PATH = 'data/export/retrain_all_labeled_2865.json'
```

### 4️⃣ Kiểm tra dữ liệu
```bash
# Kiểm tra TikTok data
python check_tvu_data.py

# Phân tích dữ liệu hợp nhất
python analyze_merged_data.py

# Xác thực dữ liệu
python _verify_data.py

# Trực quan hóa
python visualize_data.py
```

### 5️⃣ Xuất dữ liệu YouTube
```bash
python export_youtube_data.py
```

### 6️⃣ Merge comments từ Apify
```bash
python merge_apify_comments.py
```

## 📁 Cấu trúc Project

```
tiktok_analytics/
├── modules/                      # Thư viện chính
│   ├── tiktok_scraper.py        # Scraper TikTok
│   ├── youtube_scraper.py       # Scraper YouTube
│   ├── sentiment_analyzer.py    # Phân tích sentiment (PhoBERT, Gemini, etc.)
│   └── metrics_analyzer.py      # Phân tích metrics
│
├── pipeline/                     # Quy trình xử lý dữ liệu
│   ├── data_collector.py        # Thu thập dữ liệu
│   ├── data_importer.py         # Import dữ liệu
│   ├── data_cleaner.py          # Làm sạch dữ liệu
│   ├── data_labeler.py          # Đánh dấu nhãn (labeling)
│   ├── data_validator.py        # Kiểm tra tính hợp lệ
│   ├── data_exporter.py         # Xuất dữ liệu
│   ├── apify_importer.py        # Import từ Apify
│   └── pipeline_orchestrator.py # Điều phối quy trình
│
├── database/                     # Mô hình database
│   └── models.py
│
├── data/                         # Dữ liệu
│   ├── raw/                      # Dữ liệu thô
│   ├── cleaned/                  # Dữ liệu đã làm sạch
│   ├── labeled/                  # Dữ liệu đã đánh dấu
│   ├── merged/                   # Dữ liệu hợp nhất
│   ├── validated/                # Dữ liệu đã xác thực
│   ├── export/                   # Dataset export để train
│   └── reports/                  # Báo cáo phân tích
│
├── phobert_tvu_sentiment/        # Mô hình PhoBERT đã tinh chỉnh
│   ├── config.json
│   ├── model files (BPE, vocab...)
│   └── README.md
│
├── models/                       # Mô hình đã lưu
│   └── [model_name]/
│       ├── config.json
│       ├── model.safetensors
│       └── training_metadata.json
│
├── reports/                      # Báo cáo và output
│   └── *.txt, *.pdf, *.pptx
│
├── phobert_finetune.ipynb       # Notebook huấn luyện PhoBERT
├── dashboard.py                  # Dashboard Streamlit
├── create_pptx_report.py        # Tạo báo cáo PPTX
├── config.py                     # Cấu hình chung
├── requirements.txt              # Dependencies
├── .env.example                  # Template biến môi trường
├── .gitignore
└── README.md
```

### 📊 Dữ liệu Chính
- **Training data**: 2004 comments đã đánh dấu thủ công
- **Pseudo-labeled**: 778 comments từ mô hình v1
- **Tổng**: 2865 comments qua xử lý
- **Split**: 70% train, 15% val, 15% test

## 📊 Kết quả mô hình

### PhoBERT Sentiment Analysis (Manual-only)
- **Tập kiểm tra**: 301 comments
- **Accuracy**: 72.43% (baseline), 72.43% (tuned)
- **F1-score (macro)**: 0.5418 (baseline), 0.5418 (tuned)

### Manual Benchmark (Dashboard-compatible)
- **Tập benchmark**: 2004 comments đã đánh dấu
- **Accuracy**: 78.29%
- **F1-score (weighted)**: 0.7766
- **F1-score (macro)**: 0.7470

### Chi tiết theo lớp
| Lớp | Precision | Recall | F1-score |
|-----|-----------|--------|----------|
| Positive | 0.72 | 0.71 | 0.72 |
| Neutral | 0.85 | 0.82 | 0.83 |
| Negative | 0.68 | 0.71 | 0.69 |

## 🎯 Metadata mô hình

Mỗi phiên bản mô hình lưu trữ `training_metadata.json` chứa:
- **Training info**: train_sources, train_size, val_size, test_size
- **Model config**: max_length, epochs, learning_rate, batch_size, label_smoothing
- **Evaluation metrics**: holdout_test_metrics, manual_benchmark_metrics
- **Reporting note**: Giải thích sự khác biệt giữa 2 metric sets

## 🔧 Công cụ & Dependencies chính

```
PyTorch 1.x              # Deep learning framework
Transformers 4.47.0+     # Hugging Face models
scikit-learn             # Metrics & preprocessing
Pandas & NumPy           # Data manipulation
Streamlit                # Dashboard framework
Matplotlib & Seaborn     # Visualization
python-pptx              # Report generation
```

## 📝 Ghi chú

### Semi-supervised Learning (Học bán giám sát)
Dự án sử dụng self-training:
1. Labeldata thủ công 2004 comments (high confidence)
2. Train mô hình v1 trên 2004 mẫu
3. Sử dụng v1 để tự động dán nhãn 778 comments (pseudo-label)
4. Train mô hình final trên 2782 mẫu (manual + pseudo)
5. Hoặc train riêng trên 2004 mẫu (manual only) để so sánh

### Khác biệt Evaluation Metrics
- **Hold-out test metrics**: Đo trên tập test (301 mẫu) - đo năng lực generalization
- **Manual benchmark metrics**: Đo trên tập manual (2004 mẫu) - so sánh với dashboard
- Chi tiết xem `training_metadata.json` trong model folder

## 🤝 Cùng tham gia

Để báo cáo lỗi hoặc đề xuất tính năng, vui lòng:
1. Fork repository
2. Tạo branch feature (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

Dự án này được phát hành dưới giấy phép MIT. Xem [LICENSE](LICENSE) để chi tiết.

## 👤 Thông tin tác giả

**Sinh viên thực tập**  
Trường Đại học Trà Vinh  
GitHub: [@LeTuanKhaTTD](https://github.com/LeTuanKhaTTD)

---

**Last Updated**: March 2026  
**Mô hình PhoBERT**: `vinai/phobert-base` (Hugging Face)  
**Dữ liệu**: TikTok account @travinhuniversity

