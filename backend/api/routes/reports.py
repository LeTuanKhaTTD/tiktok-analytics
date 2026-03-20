from collections import Counter

from fastapi import APIRouter, Depends

from backend.api.deps import get_current_user
from backend.db.supabase_client import get_supabase_client
from backend.schemas.report import ReportCreateRequest
from backend.services.report_service import build_report_summary

router = APIRouter()


@router.post("/create")
def create_report(payload: ReportCreateRequest, current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    data = {
        "user_id": current_user["id"],
        "title": payload.title,
        "summary": payload.summary,
        "metrics": payload.metrics,
    }
    inserted = supabase.table("report_history").insert(data).execute()
    return {"item": inserted.data[0]}


@router.post("/create-latest")
def create_latest_report(current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    res = (
        supabase.table("analysis_results")
        .select("sentiment")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .limit(200)
        .execute()
    )
    rows = res.data or []
    counter = Counter([x.get("sentiment", "neutral") for x in rows])
    metrics = {
        "total": len(rows),
        "positive": counter.get("positive", 0),
        "neutral": counter.get("neutral", 0),
        "negative": counter.get("negative", 0),
    }
    title = "Bao cao phan tich gan nhat"
    summary = build_report_summary(metrics)

    inserted = supabase.table("report_history").insert(
        {
            "user_id": current_user["id"],
            "title": title,
            "summary": summary,
            "metrics": metrics,
        }
    ).execute()
    return {"item": inserted.data[0]}


@router.get("/history")
def report_history(limit: int = 30, current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    res = (
        supabase.table("report_history")
        .select("id,title,summary,metrics,created_at")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"items": res.data or []}
