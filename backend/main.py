from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import auth, analysis, reports
from backend.core.config import settings

app = FastAPI(title="TVU TikTok Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok", "service": "backend"}
