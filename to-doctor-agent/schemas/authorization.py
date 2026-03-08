"""
schemas/authorization.py
授权相关 Pydantic 模型
"""
from pydantic import BaseModel
from typing import Optional


class AuthRequest(BaseModel):
    doctor_id: str
    patient_id: str
    reason: str = ""


class AuthGrant(BaseModel):
    auth_id: str
    patient_id: str
    granted: bool
    report_id: Optional[str] = None


class AuthResponse(BaseModel):
    auth_id: str
    status: str
    doctor_id: str
    patient_id: str
