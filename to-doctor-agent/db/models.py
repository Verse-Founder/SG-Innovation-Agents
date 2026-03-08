"""
db/models.py
SQLAlchemy 2.0 ORM — to-doctor-agent 新增表
共享 task-agent 的数据库，通过 DoctorBase 管理本模块的表
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Text, Float, Integer, DateTime, Boolean, JSON,
    ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


class DoctorBase(DeclarativeBase):
    """to-doctor-agent 专用的 Base，与 task-agent 的 Base 分离"""
    pass


# ── 报告 ─────────────────────────────────────────────────

class MedicalReport(DoctorBase):
    """生成的医疗报告"""
    __tablename__ = "medical_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    request_id: Mapped[Optional[str]] = mapped_column(String(36), unique=True, nullable=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    report_type: Mapped[str] = mapped_column(String(32), default="comprehensive")
    status: Mapped[str] = mapped_column(String(20), default="generating")
    # status: generating / completed / failed / data_incomplete

    # 报告内容
    data_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # 数据覆盖范围
    data_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_completeness: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


# ── 授权 ─────────────────────────────────────────────────

class ReportAuthorization(DoctorBase):
    """报告授权记录"""
    __tablename__ = "report_authorizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    doctor_id: Mapped[str] = mapped_column(String(64), index=True)
    patient_id: Mapped[str] = mapped_column(String(64), index=True)
    report_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # status: pending / granted / denied / expired

    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    granted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


# ── 处方 ─────────────────────────────────────────────────

class Prescription(DoctorBase):
    """处方记录（mock HIS 对接）"""
    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String(64), index=True)
    doctor_id: Mapped[str] = mapped_column(String(64))
    medication_name: Mapped[str] = mapped_column(String(128))
    dosage: Mapped[str] = mapped_column(String(64))
    frequency: Mapped[str] = mapped_column(String(64))
    duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


# ── 预约建议 ─────────────────────────────────────────────

class AppointmentSuggestion(DoctorBase):
    """预约建议"""
    __tablename__ = "appointment_suggestions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    department: Mapped[str] = mapped_column(String(64))
    urgency: Mapped[str] = mapped_column(String(20), default="routine")
    # urgency: routine / recommended / urgent

    reason: Mapped[str] = mapped_column(Text)
    suggested_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # status: pending / booked / dismissed

    report_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


# ── 审计日志 ─────────────────────────────────────────────

class AuditLog(DoctorBase):
    """审计日志 — 记录所有敏感操作"""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    action: Mapped[str] = mapped_column(String(64))
    # action: report_generated / auth_requested / auth_granted /
    #         auth_denied / prescription_created / report_accessed

    actor_id: Mapped[str] = mapped_column(String(64))
    actor_type: Mapped[str] = mapped_column(String(20))  # patient / doctor / system
    target_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
