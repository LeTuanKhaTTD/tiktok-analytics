from pydantic import BaseModel, Field


class AnalyzeTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class AnalyzeTextResponse(BaseModel):
    sentiment: str
    confidence: float
    model: str
    raw_response: dict


class AnalysisHistoryItem(BaseModel):
    id: str
    text: str
    sentiment: str
    confidence: float
    created_at: str
