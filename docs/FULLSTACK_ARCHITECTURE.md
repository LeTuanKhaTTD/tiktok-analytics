# Full-stack Architecture (Streamlit + FastAPI + Supabase + HuggingFace)

## Components

- Frontend Streamlit: `frontend/app.py`
  - Registration / Login
  - Analysis dashboard
  - Report history

- Backend FastAPI: `backend/main.py`
  - Authentication (JWT)
  - PhoBERT analysis via HuggingFace Inference API
  - Save analysis and report history to Supabase

- Database (Supabase)
  - `app_users`
  - `analysis_results`
  - `report_history`

- SQL schema
  - `sql/supabase_schema.sql`

## API Endpoints

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/analysis/text`
- `GET /api/analysis/history`
- `POST /api/reports/create-latest`
- `GET /api/reports/history`
- `GET /api/health`

## Run local

1. Install dependencies:

```powershell
pip install -r requirements-fullstack.txt
```

2. Configure `.env` from `.env.example`

3. Run backend:

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

4. Run frontend:

```powershell
streamlit run frontend/app.py
```

## Notes

- This full-stack module is added in parallel and does not remove existing `dashboard.py`.
- For production, move password auth to Supabase Auth or external identity provider.
- For production, add Row-Level Security policies in Supabase.
