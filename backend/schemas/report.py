from pydantic import BaseModel


class ReportCreateRequest(BaseModel):
    title: str
    summary: str
    metrics: dict


class ReportItem(BaseModel):
    id: str
    title: str
    summary: str
    metrics: dict
    created_at: str
