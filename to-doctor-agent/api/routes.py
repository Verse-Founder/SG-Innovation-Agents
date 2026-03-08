"""
api/routes.py
FastAPI 路由 — 报告/授权/预约/处方
"""
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from db.session import get_session
from db import crud
from graph.builder import run_report_pipeline
from engine.prescription_manager import validate_prescription, format_prescription_for_task_agent
from schemas.report import ReportGenerateRequest, ReportResponse
from schemas.authorization import AuthRequest, AuthGrant
from schemas.prescription import PrescriptionCreate

logger = logging.getLogger(__name__)
router = APIRouter()


# ── 报告路由 ─────────────────────────────────────────────

@router.post("/reports/generate")
async def generate_report(req: ReportGenerateRequest):
    """患者生成报告（支持幂等：相同 request_id 返回已有报告）"""
    async with get_session() as session:
        # 幂等检查
        report = await crud.create_report(
            session, user_id=req.user_id, report_type=req.report_type,
            request_id=req.request_id,
        )

        if report.status == "completed":
            return {
                "status": "ok",
                "data": {
                    "report_id": report.id,
                    "status": report.status,
                    "summary": report.summary,
                    "message": "报告已存在（幂等返回）",
                },
            }

        # 运行生成流水线
        try:
            result = run_report_pipeline(req.user_id, days=req.days)
            await crud.update_report_content(
                session,
                report_id=report.id,
                data_json=result["report_data"],
                summary=result["summary"],
                pdf_path=result.get("pdf_path"),
                data_completeness=result.get("data_completeness"),
            )

            # 保存预约建议
            for appt in result.get("appointment_suggestions", []):
                await crud.create_appointment_suggestion(
                    session, user_id=req.user_id,
                    department=appt["department"],
                    reason=appt["reason"],
                    urgency=appt.get("urgency", "routine"),
                    suggested_date=appt.get("suggested_date"),
                    report_id=report.id,
                )

            # 审计日志
            await crud.log_audit(
                session, action="report_generated",
                actor_id=req.user_id, actor_type="patient",
                target_id=report.id,
            )

            return {
                "status": "ok",
                "data": {
                    "report_id": report.id,
                    "status": "completed",
                    "summary": result["summary"],
                    "data_completeness": result.get("data_completeness", {}),
                    "appointment_count": len(result.get("appointment_suggestions", [])),
                    "pdf_available": bool(result.get("pdf_path")),
                },
            }

        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            await crud.mark_report_failed(session, report.id, str(e))
            raise HTTPException(status_code=500, detail=f"报告生成失败: {e}")


@router.get("/reports/{report_id}")
async def get_report(report_id: str, viewer_id: Optional[str] = None):
    """查看报告（JSON）"""
    async with get_session() as session:
        report = await crud.get_report(session, report_id)
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")

        # 权限检查：自己或已授权的医生
        if viewer_id and viewer_id != report.user_id:
            has_access = await crud.check_doctor_access(session, viewer_id, report.user_id)
            if not has_access:
                await crud.log_audit(
                    session, action="unauthorized_access",
                    actor_id=viewer_id, actor_type="doctor",
                    target_id=report_id, details="越权访问被拦截",
                )
                raise HTTPException(status_code=403, detail="无权查看此报告")
            await crud.log_audit(
                session, action="report_accessed",
                actor_id=viewer_id, actor_type="doctor",
                target_id=report_id,
            )

        return {
            "status": "ok",
            "data": {
                "report_id": report.id,
                "user_id": report.user_id,
                "report_type": report.report_type,
                "status": report.status,
                "summary": report.summary,
                "data": json.loads(report.data_json) if report.data_json else None,
                "created_at": report.created_at.isoformat() if report.created_at else None,
            },
        }


@router.get("/reports/{report_id}/pdf")
async def download_report_pdf(report_id: str):
    """下载报告 PDF"""
    async with get_session() as session:
        report = await crud.get_report(session, report_id)
        if not report or not report.pdf_path:
            raise HTTPException(status_code=404, detail="PDF 不存在")
        return FileResponse(
            report.pdf_path,
            media_type="application/pdf",
            filename=f"health_report_{report.user_id}.pdf",
        )


@router.get("/reports/user/{user_id}")
async def get_user_reports(user_id: str):
    """查看用户所有报告"""
    async with get_session() as session:
        reports = await crud.get_user_reports(session, user_id)
        return {
            "status": "ok",
            "data": [
                {
                    "report_id": r.id,
                    "report_type": r.report_type,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in reports
            ],
        }


# ── 授权路由 ─────────────────────────────────────────────

@router.post("/auth/request")
async def request_authorization(req: AuthRequest):
    """医生请求授权"""
    async with get_session() as session:
        auth = await crud.create_auth_request(
            session, doctor_id=req.doctor_id,
            patient_id=req.patient_id, reason=req.reason,
        )
        await crud.log_audit(
            session, action="auth_requested",
            actor_id=req.doctor_id, actor_type="doctor",
            target_id=req.patient_id,
        )
        return {
            "status": "ok",
            "data": {
                "auth_id": auth.id,
                "status": auth.status,
                "message": "授权请求已发送，等待患者确认",
            },
        }


@router.post("/auth/grant")
async def grant_authorization(req: AuthGrant):
    """患者授予/拒绝授权"""
    async with get_session() as session:
        auth = await crud.grant_authorization(
            session, auth_id=req.auth_id, patient_id=req.patient_id,
            granted=req.granted, report_id=req.report_id,
        )
        if not auth:
            raise HTTPException(status_code=404, detail="授权请求不存在或不属于该患者")

        await crud.log_audit(
            session,
            action="auth_granted" if req.granted else "auth_denied",
            actor_id=req.patient_id, actor_type="patient",
            target_id=auth.id,
        )
        return {
            "status": "ok",
            "data": {"auth_id": auth.id, "status": auth.status},
        }


@router.get("/auth/pending/{user_id}")
async def get_pending_auth(user_id: str):
    """查看待处理授权"""
    async with get_session() as session:
        pending = await crud.get_pending_authorizations(session, user_id)
        return {
            "status": "ok",
            "data": [
                {
                    "auth_id": a.id,
                    "doctor_id": a.doctor_id,
                    "reason": a.reason,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in pending
            ],
        }


# ── 预约建议路由 ─────────────────────────────────────────

@router.get("/appointments/{user_id}")
async def get_appointments(user_id: str):
    """获取预约建议"""
    async with get_session() as session:
        appointments = await crud.get_user_appointments(session, user_id)
        return {
            "status": "ok",
            "data": [
                {
                    "id": a.id,
                    "department": a.department,
                    "urgency": a.urgency,
                    "reason": a.reason,
                    "suggested_date": a.suggested_date,
                    "status": a.status,
                }
                for a in appointments
            ],
        }


# ── 处方路由 ─────────────────────────────────────────────

@router.post("/prescriptions")
async def create_prescription(req: PrescriptionCreate):
    """记录处方（mock HIS 对接）"""
    # 验证处方
    validation = validate_prescription(req.medication_name, req.dosage, req.frequency)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    async with get_session() as session:
        rx = await crud.create_prescription(
            session,
            patient_id=req.patient_id,
            doctor_id=req.doctor_id,
            medication_name=req.medication_name,
            dosage=req.dosage,
            frequency=req.frequency,
            duration_days=req.duration_days,
            notes=req.notes,
        )
        await crud.log_audit(
            session, action="prescription_created",
            actor_id=req.doctor_id, actor_type="doctor",
            target_id=rx.id,
        )
        return {
            "status": "ok",
            "data": {
                "prescription_id": rx.id,
                "warnings": validation.get("warnings", []),
                "task_agent_payload": format_prescription_for_task_agent(
                    req.patient_id, req.medication_name,
                    req.dosage, req.frequency, req.doctor_id,
                ),
            },
        }


@router.get("/prescriptions/{user_id}")
async def get_prescriptions(user_id: str, active_only: bool = True):
    """查看处方历史"""
    async with get_session() as session:
        prescriptions = await crud.get_patient_prescriptions(session, user_id, active_only)
        return {
            "status": "ok",
            "data": [
                {
                    "id": rx.id,
                    "medication_name": rx.medication_name,
                    "dosage": rx.dosage,
                    "frequency": rx.frequency,
                    "is_active": rx.is_active,
                    "notes": rx.notes,
                }
                for rx in prescriptions
            ],
        }


# ── 健康检查 ─────────────────────────────────────────────

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "to-doctor-agent"}
