"""
db/crud.py
数据库 CRUD — 报告/授权/处方/预约/审计
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    MedicalReport, ReportAuthorization, Prescription,
    AppointmentSuggestion, AuditLog,
)


# ── 报告 CRUD ────────────────────────────────────────────

async def create_report(
    session: AsyncSession,
    user_id: str,
    report_type: str = "comprehensive",
    request_id: Optional[str] = None,
    data_start: Optional[datetime] = None,
    data_end: Optional[datetime] = None,
) -> MedicalReport:
    existing = None
    if request_id:
        result = await session.execute(
            select(MedicalReport).where(MedicalReport.request_id == request_id)
        )
        existing = result.scalar_one_or_none()
    if existing:
        return existing  # 幂等：相同 request_id 返回已有报告

    report = MedicalReport(
        id=str(uuid.uuid4()),
        request_id=request_id,
        user_id=user_id,
        report_type=report_type,
        status="generating",
        data_start_date=data_start,
        data_end_date=data_end,
    )
    session.add(report)
    await session.flush()
    return report


async def update_report_content(
    session: AsyncSession,
    report_id: str,
    data_json: dict,
    summary: str,
    pdf_path: Optional[str] = None,
    data_completeness: Optional[dict] = None,
) -> Optional[MedicalReport]:
    result = await session.execute(
        select(MedicalReport).where(MedicalReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        return None

    report.data_json = json.dumps(data_json, ensure_ascii=False)
    report.summary = summary
    report.pdf_path = pdf_path
    report.status = "completed"
    if data_completeness:
        report.data_completeness = json.dumps(data_completeness, ensure_ascii=False)
    report.updated_at = datetime.utcnow()
    await session.flush()
    return report


async def mark_report_failed(
    session: AsyncSession, report_id: str, reason: str = "",
) -> None:
    await session.execute(
        update(MedicalReport)
        .where(MedicalReport.id == report_id)
        .values(status="failed", summary=f"生成失败: {reason}", updated_at=datetime.utcnow())
    )
    await session.flush()


async def get_report(session: AsyncSession, report_id: str) -> Optional[MedicalReport]:
    result = await session.execute(
        select(MedicalReport).where(MedicalReport.id == report_id)
    )
    return result.scalar_one_or_none()


async def get_user_reports(
    session: AsyncSession, user_id: str, limit: int = 20,
) -> list[MedicalReport]:
    stmt = (
        select(MedicalReport)
        .where(MedicalReport.user_id == user_id)
        .order_by(MedicalReport.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ── 授权 CRUD ────────────────────────────────────────────

async def create_auth_request(
    session: AsyncSession,
    doctor_id: str,
    patient_id: str,
    reason: str = "",
) -> ReportAuthorization:
    auth = ReportAuthorization(
        id=str(uuid.uuid4()),
        doctor_id=doctor_id,
        patient_id=patient_id,
        reason=reason,
        status="pending",
    )
    session.add(auth)
    await session.flush()
    return auth


async def grant_authorization(
    session: AsyncSession,
    auth_id: str,
    patient_id: str,
    granted: bool,
    report_id: Optional[str] = None,
) -> Optional[ReportAuthorization]:
    result = await session.execute(
        select(ReportAuthorization).where(ReportAuthorization.id == auth_id)
    )
    auth = result.scalar_one_or_none()
    if not auth or auth.patient_id != patient_id:
        return None

    auth.status = "granted" if granted else "denied"
    auth.granted_at = datetime.utcnow() if granted else None
    auth.expires_at = datetime.utcnow() + timedelta(days=30) if granted else None
    auth.report_id = report_id
    await session.flush()
    return auth


async def check_doctor_access(
    session: AsyncSession, doctor_id: str, patient_id: str,
) -> bool:
    result = await session.execute(
        select(ReportAuthorization).where(
            ReportAuthorization.doctor_id == doctor_id,
            ReportAuthorization.patient_id == patient_id,
            ReportAuthorization.status == "granted",
        )
    )
    auth = result.scalar_one_or_none()
    if not auth:
        return False
    if auth.expires_at and auth.expires_at < datetime.utcnow():
        auth.status = "expired"
        await session.flush()
        return False
    return True


async def get_pending_authorizations(
    session: AsyncSession, patient_id: str,
) -> list[ReportAuthorization]:
    result = await session.execute(
        select(ReportAuthorization)
        .where(
            ReportAuthorization.patient_id == patient_id,
            ReportAuthorization.status == "pending",
        )
        .order_by(ReportAuthorization.created_at.desc())
    )
    return list(result.scalars().all())


# ── 处方 CRUD ────────────────────────────────────────────

async def create_prescription(
    session: AsyncSession,
    patient_id: str,
    doctor_id: str,
    medication_name: str,
    dosage: str,
    frequency: str,
    duration_days: Optional[int] = None,
    notes: Optional[str] = None,
) -> Prescription:
    rx = Prescription(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        doctor_id=doctor_id,
        medication_name=medication_name,
        dosage=dosage,
        frequency=frequency,
        duration_days=duration_days,
        notes=notes,
    )
    session.add(rx)
    await session.flush()
    return rx


async def get_patient_prescriptions(
    session: AsyncSession, patient_id: str, active_only: bool = True,
) -> list[Prescription]:
    stmt = select(Prescription).where(Prescription.patient_id == patient_id)
    if active_only:
        stmt = stmt.where(Prescription.is_active == True)
    stmt = stmt.order_by(Prescription.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ── 预约建议 CRUD ────────────────────────────────────────

async def create_appointment_suggestion(
    session: AsyncSession,
    user_id: str,
    department: str,
    reason: str,
    urgency: str = "routine",
    suggested_date: Optional[str] = None,
    report_id: Optional[str] = None,
) -> AppointmentSuggestion:
    appt = AppointmentSuggestion(
        id=str(uuid.uuid4()),
        user_id=user_id,
        department=department,
        reason=reason,
        urgency=urgency,
        suggested_date=suggested_date,
        report_id=report_id,
    )
    session.add(appt)
    await session.flush()
    return appt


async def get_user_appointments(
    session: AsyncSession, user_id: str,
) -> list[AppointmentSuggestion]:
    result = await session.execute(
        select(AppointmentSuggestion)
        .where(AppointmentSuggestion.user_id == user_id)
        .order_by(AppointmentSuggestion.created_at.desc())
    )
    return list(result.scalars().all())


# ── 审计日志 CRUD ────────────────────────────────────────

async def log_audit(
    session: AsyncSession,
    action: str,
    actor_id: str,
    actor_type: str = "system",
    target_id: Optional[str] = None,
    details: Optional[str] = None,
) -> AuditLog:
    entry = AuditLog(
        id=str(uuid.uuid4()),
        action=action,
        actor_id=actor_id,
        actor_type=actor_type,
        target_id=target_id,
        details=details,
    )
    session.add(entry)
    await session.flush()
    return entry
