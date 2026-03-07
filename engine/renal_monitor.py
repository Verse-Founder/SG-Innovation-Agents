"""
engine/renal_monitor.py
肾功能专项监测

糖尿病患者往往伴随肾功能衰竭风险：
- eGFR 下降趋势检测
- 蛋白尿 / 泡沫尿检测
- 症状关联（口干、疲劳、夜尿增多）
"""
from schemas.health import HealthSnapshot, RenalIndicators
from config import settings


def assess_renal_status(snapshot: HealthSnapshot) -> dict:
    """
    评估肾功能状态
    返回 {
        "concern_level": "none" / "watch" / "warning" / "critical",
        "findings": [...],
        "recommendations": [...],
    }
    """
    renal = snapshot.renal
    findings = []
    recommendations = []
    concern_level = "none"

    # ── eGFR 分级 ──
    if renal.egfr is not None:
        if renal.egfr < settings.EGFR_KIDNEY_FAILURE:
            concern_level = "critical"
            findings.append(f"eGFR {renal.egfr} mL/min/1.73m²：严重肾功能不全（肾衰竭范围）")
            recommendations.append("紧急就医")
        elif renal.egfr < settings.EGFR_SEVERE_DECLINE:
            concern_level = "critical"
            findings.append(f"eGFR {renal.egfr}：重度下降")
            recommendations.append("尽快预约肾内科")
        elif renal.egfr < settings.EGFR_MODERATE_DECLINE:
            concern_level = "warning"
            findings.append(f"eGFR {renal.egfr}：中度下降")
            recommendations.append("建议 1-2 周内复诊肾内科")
        elif renal.egfr < settings.EGFR_MILD_DECLINE:
            concern_level = "warning" if concern_level == "none" else concern_level
            findings.append(f"eGFR {renal.egfr}：轻度下降")
            recommendations.append("建议近期测尿蛋白并复查")
        elif renal.egfr < settings.EGFR_NORMAL:
            concern_level = "watch" if concern_level == "none" else concern_level
            findings.append(f"eGFR {renal.egfr}：轻微低于正常")

        # eGFR 下降趋势
        if renal.egfr_previous is not None and renal.egfr is not None:
            decline = renal.egfr_previous - renal.egfr
            if decline > settings.EGFR_DECLINE_ALERT_THRESHOLD:
                concern_level = max_concern(concern_level, "warning")
                findings.append(f"eGFR 3 个月内下降 {decline:.1f}（>{settings.EGFR_DECLINE_ALERT_THRESHOLD}）")
                recommendations.append("eGFR 下降趋势明显，需医生评估是否调整治疗方案")

    # ── 蛋白尿 ──
    if renal.proteinuria is not None and renal.proteinuria > 30:
        concern_level = max_concern(concern_level, "warning")
        findings.append(f"蛋白尿 {renal.proteinuria} mg/day（正常 <30）")
        recommendations.append("注意蛋白质摄入量，避免高蛋白饮食")

    # ── 泡沫尿 ──
    if renal.has_foam_urine:
        concern_level = max_concern(concern_level, "watch")
        findings.append("用户报告泡沫尿（可能提示蛋白尿/肾损害）")
        recommendations.append("建议测尿蛋白/肌酐比值排查")

    # ── 症状关联 ──
    renal_symptoms = {"口干", "容易疲劳", "疲劳", "夜尿增多", "水肿", "浮肿"}
    matched_symptoms = [s for s in snapshot.reported_symptoms if s in renal_symptoms]
    if matched_symptoms:
        concern_level = max_concern(concern_level, "watch")
        findings.append(f"用户自报症状可能与肾功能相关：{', '.join(matched_symptoms)}")

    return {
        "concern_level": concern_level,
        "findings": findings,
        "recommendations": recommendations,
    }


def max_concern(current: str, new: str) -> str:
    """取更高的关注级别"""
    levels = {"none": 0, "watch": 1, "warning": 2, "critical": 3}
    return current if levels.get(current, 0) >= levels.get(new, 0) else new
