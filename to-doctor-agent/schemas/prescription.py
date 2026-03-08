"""
schemas/prescription.py
处方相关 Pydantic 模型
"""
from pydantic import BaseModel
from typing import Optional


class PrescriptionCreate(BaseModel):
    patient_id: str
    doctor_id: str
    medication_name: str
    dosage: str
    frequency: str
    duration_days: Optional[int] = None
    notes: Optional[str] = None


class PrescriptionResponse(BaseModel):
    id: str
    patient_id: str
    medication_name: str
    dosage: str
    frequency: str
    is_active: bool
