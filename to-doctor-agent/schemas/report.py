"""
schemas/report.py
报告相关 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional


class ReportGenerateRequest(BaseModel):
    user_id: str
    report_type: str = "comprehensive"
    request_id: Optional[str] = None
    days: int = Field(default=30, ge=7, le=365)


class ReportResponse(BaseModel):
    report_id: str
    status: str
    user_id: str
    report_type: str
    summary: Optional[str] = None
    data: Optional[dict] = None
    pdf_url: Optional[str] = None
    created_at: Optional[str] = None
