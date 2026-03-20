from fastapi import APIRouter, Depends

from backend.api.deps import get_current_user
from backend.db.supabase_client import get_supabase_client
from backend.schemas.analysis import AnalyzeTextRequest, AnalyzeTextResponse
from backend.services.phobert_api import analyze_with_huggingface

router = APIRouter()


@router.post("/text", response_model=AnalyzeTextResponse)
def analyze_text(payload: AnalyzeTextRequest, current_user: dict = Depends(get_current_user)):
    result = analyze_with_huggingface(payload.text)

    supabase = get_supabase_client()
    supabase.table("analysis_results").insert(
        {
            "user_id": current_user["id"],
            "text": payload.text,
            "sentiment": result["sentiment"],
            "confidence": result["confidence"],
            "model": result["model"],
            "raw_response": result["raw_response"],
        }
    ).execute()

    return AnalyzeTextResponse(**result)


@router.get("/history")
def analysis_history(limit: int = 50, current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    res = (
        supabase.table("analysis_results")
        .select("id,text,sentiment,confidence,created_at")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"items": res.data or []}
