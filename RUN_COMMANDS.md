# Run Commands - TikTok Analytics

## 1) Setup moi truong (PowerShell)

```powershell
cd D:\Thuc_tap\tiktok_analytics
& D:\Thuc_tap\.venv-2\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Chay Dashboard Streamlit

```powershell
cd D:\Thuc_tap\tiktok_analytics
& D:\Thuc_tap\.venv-2\Scripts\Activate.ps1
streamlit run dashboard.py
```

Mo trinh duyet:

```text
http://localhost:8501
```

## 3) Chay Pipeline tong quat

```powershell
cd D:\Thuc_tap\tiktok_analytics
& D:\Thuc_tap\.venv-2\Scripts\Activate.ps1
python run_pipeline.py --platform tiktok --id travinhuniversity --videos 30
```

## 4) Chay Pipeline APIFY

```powershell
cd D:\Thuc_tap\tiktok_analytics
& D:\Thuc_tap\.venv-2\Scripts\Activate.ps1
python run_pipeline_apify.py
```

## 5) Chay Pipeline REAL

```powershell
cd D:\Thuc_tap\tiktok_analytics
& D:\Thuc_tap\.venv-2\Scripts\Activate.ps1
python run_pipeline_real.py
```

## 6) Xuat du lieu YouTube

```powershell
cd D:\Thuc_tap\tiktok_analytics
& D:\Thuc_tap\.venv-2\Scripts\Activate.ps1
python export_youtube_data.py
```

## 7) Merge comments APIFY

```powershell
cd D:\Thuc_tap\tiktok_analytics
& D:\Thuc_tap\.venv-2\Scripts\Activate.ps1
python merge_apify_comments.py
```

## 8) Kiem tra/phan tich nhanh du lieu

```powershell
cd D:\Thuc_tap\tiktok_analytics
& D:\Thuc_tap\.venv-2\Scripts\Activate.ps1
python check_tvu_data.py
python analyze_merged_data.py
python _verify_data.py
python visualize_data.py
```

## 9) Kiem tra GPU/PyTorch

```powershell
cd D:\Thuc_tap\tiktok_analytics
& D:\Thuc_tap\.venv-2\Scripts\Activate.ps1
python -c "import torch; print(torch.__version__); print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

## 10) Chay Notebook fine-tune PhoBERT

```powershell
cd D:\Thuc_tap\tiktok_analytics
& D:\Thuc_tap\.venv-2\Scripts\Activate.ps1
jupyter notebook phobert_finetune.ipynb
```

Neu ban chay bang VS Code, chi can mo notebook va chon kernel:

```text
D:\Thuc_tap\.venv-2\Scripts\python.exe
```

## 11) Dung Streamlit

Trong terminal dang chay app:

```powershell
Ctrl + C
```

Hoac stop toan bo process Streamlit:

```powershell
Get-Process -Name streamlit -ErrorAction SilentlyContinue | Stop-Process -Force
```

## 12) Kiem tra cong 8501 dang mo

```powershell
Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue |
  Select-Object LocalAddress, LocalPort, OwningProcess
```

## 13) Chuan bi data train lai (manual-only va manual+phobert)

```powershell
cd D:\Thuc_tap\tiktok_analytics
& D:\Thuc_tap\.venv-2\Scripts\Activate.ps1
python prepare_retrain_datasets.py
```

Sau khi chay xong se tao 2 file:

```text
data/export/retrain_manual_only_2004.json
data/export/retrain_manual_phobert_2782.json
data/export/retrain_all_labeled_2865.json
```

## 14) Train lai trong notebook theo 2 kich ban

Trong `phobert_finetune.ipynb`:

1) Kich ban A (manual-only 2004):
- `STRICT_MANUAL_ONLY = True`
- `TRAIN_SOURCES = ['manual']`
- `DATA_PATH = 'data/export/retrain_manual_only_2004.json'`

2) Kich ban B (manual + phobert 2782):
- `STRICT_MANUAL_ONLY = False`
- `TRAIN_SOURCES = ['manual', 'phobert']`
- `DATA_PATH = 'data/export/retrain_manual_phobert_2782.json'`

3) Kich ban C (toan bo 2865 da gan nhan):
- `STRICT_MANUAL_ONLY = False`
- `TRAIN_SOURCES = ['manual', 'phobert']`
- `DATA_PATH = 'data/export/retrain_all_labeled_2865.json'`

Kich ban C da chuan hoa `method` trong file export de khong bi roi mat 83 dong method trong.
