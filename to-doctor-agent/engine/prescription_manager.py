"""
engine/prescription_manager.py
处方管理 — mock HIS 对接
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def validate_prescription(
    medication_name: str,
    dosage: str,
    frequency: str,
) -> dict:
    """验证处方合理性（mock）"""
    warnings = []

    # 基础校验
    if not medication_name.strip():
        return {"valid": False, "error": "药物名称不能为空"}
    if not dosage.strip():
        return {"valid": False, "error": "剂量不能为空"}

    # 常见糖尿病药物交叉检查（mock）
    KNOWN_DIABETES_MEDS = {
        "metformin": {"max_daily_mg": 2000, "note": "肾功能不全患者慎用"},
        "glipizide": {"max_daily_mg": 40, "note": "注意低血糖风险"},
        "insulin_glargine": {"note": "长效胰岛素，每日一次"},
        "empagliflozin": {"note": "SGLT2 抑制剂，注意泌尿系感染"},
        "sitagliptin": {"max_daily_mg": 100, "note": "DPP-4 抑制剂"},
    }

    med_lower = medication_name.lower().replace(" ", "_")
    if med_lower in KNOWN_DIABETES_MEDS:
        info = KNOWN_DIABETES_MEDS[med_lower]
        if info.get("note"):
            warnings.append(info["note"])

    return {"valid": True, "warnings": warnings}


def format_prescription_for_task_agent(
    patient_id: str,
    medication_name: str,
    dosage: str,
    frequency: str,
    doctor_id: str,
) -> dict:
    """格式化处方为 task-agent 可接收的任务触发格式"""
    return {
        "user_id": patient_id,
        "trigger_source": "doctor",
        "payload": {
            "type": "prescription",
            "medication_name": medication_name,
            "dosage": dosage,
            "frequency": frequency,
            "doctor_id": doctor_id,
            "action": "create_medication_reminder",
        },
    }


# ── Mock HIS 接口 ────────────────────────────────────────

class MockHISClient:
    """模拟医院信息系统（HIS）客户端"""

    def __init__(self):
        self._prescriptions = []

    async def fetch_prescriptions(self, patient_id: str) -> list[dict]:
        """从 HIS 拉取处方（mock）"""
        logger.info(f"[MockHIS] 拉取患者 {patient_id} 处方")
        return [
            {
                "medication_name": "Metformin",
                "dosage": "500mg",
                "frequency": "每日两次，随餐",
                "doctor_id": "dr_mock_001",
                "notes": "肾功能正常可用",
            },
        ]

    async def submit_report(self, patient_id: str, report_data: dict) -> dict:
        """提交报告到 HIS（mock）"""
        logger.info(f"[MockHIS] 提交患者 {patient_id} 报告")
        return {"status": "accepted", "his_reference_id": "HIS-MOCK-001"}


mock_his = MockHISClient()
