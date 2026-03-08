"""
engine/report_generator.py
报告生成引擎 — 聚合患者数据，生成结构化医疗报告
"""
import json
import logging
from datetime import datetime
from typing import Optional

from engine.trend_analyzer import generate_full_trend_analysis
from engine.appointment_advisor import generate_appointment_suggestions
from engine.data_masker import mask_report_data

logger = logging.getLogger(__name__)


def generate_report_data(
    user_id: str,
    health_logs: list[dict],
    behavior_patterns: list[dict],
    task_data: dict,
    prescriptions: list[dict] = None,
    user_profile: dict = None,
) -> dict:
    """生成完整报告数据"""

    # 1. 趋势分析
    trend_analysis = generate_full_trend_analysis(
        health_logs=health_logs,
        behavior_patterns=behavior_patterns,
        task_data=task_data,
    )

    # 2. 预约建议
    appointments = generate_appointment_suggestions(
        trend_analysis=trend_analysis,
        existing_prescriptions=prescriptions,
    )

    # 3. 组装报告
    report = {
        "report_metadata": {
            "patient_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
            "data_period_days": 30,
            "data_completeness": trend_analysis["data_completeness"],
            "is_data_complete": trend_analysis["is_complete"],
        },
        "patient_profile": user_profile or {"patient_id": user_id},
        "glucose_analysis": trend_analysis["glucose_trend"],
        "renal_function": trend_analysis["egfr_trend"],
        "medication_adherence": trend_analysis["medication_adherence"],
        "activity_summary": trend_analysis["activity_trend"],
        "task_completion": trend_analysis["task_completion"],
        "appointment_suggestions": appointments,
        "current_prescriptions": prescriptions or [],
    }

    # 4. 数据脱敏
    report = mask_report_data(report)

    return report


def generate_report_summary(report_data: dict) -> str:
    """生成报告文字摘要（规则型回退，不依赖 LLM）"""
    sections = []

    # 血糖
    glucose = report_data.get("glucose_analysis", {})
    if glucose.get("status") == "analyzed":
        avg = glucose.get("average", 0)
        status_text = "控制良好" if avg < 7.8 else "偏高，需关注" if avg < 10 else "控制不佳，建议调整方案"
        sections.append(f"【血糖】近期均值 {avg} mmol/L，{status_text}。"
                       f"高血糖 {glucose.get('high_count', 0)} 次，低血糖 {glucose.get('low_count', 0)} 次。")
        if glucose.get("dawn_phenomenon"):
            sections.append("  ⚠️ 检测到黎明现象，空腹血糖偏高。")
    else:
        sections.append("【血糖】数据不完整，无法分析。")

    # eGFR
    egfr = report_data.get("renal_function", {})
    if egfr.get("status") == "analyzed":
        latest = egfr.get("latest")
        stage = egfr.get("ckd_stage", "unknown")
        sections.append(f"【肾功能】eGFR {latest} mL/min（CKD {stage} 期）。")
        if egfr.get("declining"):
            sections.append("  ⚠️ eGFR 持续下降趋势，建议肾内科随诊。")
    else:
        sections.append("【肾功能】数据不完整。")

    # 用药
    med = report_data.get("medication_adherence", {})
    if med.get("status") == "analyzed":
        pct = med.get("latest_pct", 0)
        sections.append(f"【用药依从性】{pct}%（{'良好' if pct >= 80 else '需改善'}）。")
    else:
        sections.append("【用药依从性】数据不完整。")

    # 运动
    activity = report_data.get("activity_summary", {})
    if activity.get("status") in ("analyzed", "partial"):
        steps = activity.get("avg_daily_steps", 0)
        sections.append(f"【运动】日均步数 {steps} 步。")
    else:
        sections.append("【运动】数据不完整。")

    # 任务完成
    tasks = report_data.get("task_completion", {})
    if tasks.get("status") == "analyzed":
        rate = tasks.get("completion_rate", 0)
        sections.append(f"【任务完成率】{rate}%（共 {tasks.get('total_tasks', 0)} 个任务）。")

    # 预约建议
    appointments = report_data.get("appointment_suggestions", [])
    urgent = [a for a in appointments if a.get("urgency") in ("urgent", "recommended")]
    if urgent:
        sections.append(f"【建议就诊】{len(urgent)} 项建议就诊：")
        for a in urgent:
            sections.append(f"  - {a['department']}（{a['urgency']}）：{a['reason']}")

    return "\n".join(sections)
