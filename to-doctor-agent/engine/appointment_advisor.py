"""
engine/appointment_advisor.py
智能预约建议 — 基于健康数据推荐科室和时间
"""
import logging
from datetime import datetime, timedelta

from config import settings

logger = logging.getLogger(__name__)


def generate_appointment_suggestions(
    trend_analysis: dict,
    existing_prescriptions: list[dict] = None,
) -> list[dict]:
    """基于趋势分析生成预约建议"""
    suggestions = []

    # 1. eGFR 下降 → 肾内科
    egfr = trend_analysis.get("egfr_trend", {})
    if egfr.get("declining"):
        urgency = "urgent" if egfr.get("ckd_stage") in ("G3b", "G4", "G5") else "recommended"
        suggestions.append({
            "department": "肾内科",
            "urgency": urgency,
            "reason": f"eGFR 持续下降（当前 {egfr.get('latest')} mL/min，CKD {egfr.get('ckd_stage')} 期），建议尽快就诊评估肾功能",
            "suggested_date": _suggest_date(urgency),
        })

    # 2. 血糖控制不佳 → 内分泌科
    glucose = trend_analysis.get("glucose_trend", {})
    if glucose.get("status") == "analyzed":
        avg = glucose.get("average", 0)
        high_count = glucose.get("high_count", 0)
        total = glucose.get("total_readings", 1)

        if avg > 10.0 or (high_count / max(total, 1)) > 0.5:
            suggestions.append({
                "department": "内分泌科",
                "urgency": "urgent" if avg > 13.0 else "recommended",
                "reason": f"血糖控制不佳（均值 {avg} mmol/L，高血糖 {high_count} 次/{total} 次），建议调整治疗方案",
                "suggested_date": _suggest_date("recommended"),
            })
        elif glucose.get("dawn_phenomenon"):
            suggestions.append({
                "department": "内分泌科",
                "urgency": "recommended",
                "reason": f"检测到黎明现象（空腹血糖均值 {glucose.get('fasting_average')} mmol/L），建议咨询医生调整基础胰岛素",
                "suggested_date": _suggest_date("recommended"),
            })

    # 3. 用药依从性低 → 提醒复诊
    medication = trend_analysis.get("medication_adherence", {})
    if medication.get("status") == "analyzed" and medication.get("latest_pct", 100) < 70:
        suggestions.append({
            "department": "全科/内分泌科",
            "urgency": "recommended",
            "reason": f"用药依从性偏低（{medication.get('latest_pct')}%），建议与医生沟通用药方案，是否有副作用等问题",
            "suggested_date": _suggest_date("routine"),
        })

    # 4. 常规复诊：每 3 个月 HbA1c
    suggestions.append({
        "department": "内分泌科",
        "urgency": "routine",
        "reason": "常规 HbA1c 检测（建议每 3 个月一次），评估近期血糖控制情况",
        "suggested_date": _suggest_date("routine"),
    })

    return suggestions


def _suggest_date(urgency: str) -> str:
    """根据紧急程度推荐就诊时间"""
    now = datetime.utcnow()
    if urgency == "urgent":
        target = now + timedelta(days=3)
    elif urgency == "recommended":
        target = now + timedelta(days=14)
    else:  # routine
        target = now + timedelta(days=90)

    # 跳过周末
    while target.weekday() >= 5:
        target += timedelta(days=1)

    return target.strftime("%Y-%m-%d")
