"""
engine/trend_analyzer.py
健康趋势分析 — 血糖/eGFR/用药/运动
"""
import logging
from datetime import datetime
from typing import Any

from config import settings

logger = logging.getLogger(__name__)


def analyze_glucose_trend(health_logs: list[dict]) -> dict:
    """分析血糖趋势"""
    glucose_readings = [
        log for log in health_logs
        if log.get("blood_glucose") is not None
    ]
    if not glucose_readings:
        return {"status": "no_data", "summary": "无血糖数据"}

    values = [r["blood_glucose"] for r in glucose_readings]
    fasting_values = [
        r["blood_glucose"] for r in glucose_readings
        if r.get("glucose_context") == "fasting"
    ]

    avg_glucose = sum(values) / len(values)
    max_glucose = max(values)
    min_glucose = min(values)
    std_dev = (sum((v - avg_glucose) ** 2 for v in values) / len(values)) ** 0.5

    # 黎明现象检测：空腹血糖普遍偏高
    dawn_phenomenon = False
    if fasting_values and sum(fasting_values) / len(fasting_values) > 7.0:
        dawn_phenomenon = True

    # 高血糖/低血糖次数
    high_count = sum(1 for v in values if v > settings.GLUCOSE_POSTPRANDIAL_NORMAL[1])
    low_count = sum(1 for v in values if v < settings.GLUCOSE_FASTING_NORMAL[0])

    return {
        "status": "analyzed",
        "total_readings": len(values),
        "average": round(avg_glucose, 2),
        "max": round(max_glucose, 2),
        "min": round(min_glucose, 2),
        "std_dev": round(std_dev, 2),
        "high_count": high_count,
        "low_count": low_count,
        "dawn_phenomenon": dawn_phenomenon,
        "fasting_average": round(sum(fasting_values) / len(fasting_values), 2) if fasting_values else None,
    }


def analyze_egfr_trend(health_logs: list[dict]) -> dict:
    """分析 eGFR 趋势"""
    egfr_readings = [
        log for log in health_logs
        if log.get("egfr") is not None
    ]
    if not egfr_readings:
        return {"status": "no_data", "summary": "无 eGFR 数据"}

    values = [r["egfr"] for r in egfr_readings]
    latest = values[0] if values else None

    # CKD 分期判定
    stage = "unknown"
    if latest is not None:
        for s, threshold in settings.EGFR_STAGE_THRESHOLDS.items():
            if latest >= threshold:
                stage = s
                break

    # 下降趋势检测
    declining = False
    if len(values) >= 3:
        declining = all(values[i] > values[i + 1] for i in range(min(3, len(values)) - 1))

    return {
        "status": "analyzed",
        "total_readings": len(values),
        "latest": latest,
        "ckd_stage": stage,
        "declining": declining,
        "values": values[:10],
    }


def analyze_medication_adherence(behavior_patterns: list[dict]) -> dict:
    """分析用药依从性趋势"""
    if not behavior_patterns:
        return {"status": "no_data", "summary": "无行为数据"}

    adherence_values = [
        bp.get("medication_adherence_pct", 0)
        for bp in behavior_patterns
        if bp.get("medication_adherence_pct") is not None
    ]
    if not adherence_values:
        return {"status": "no_data", "summary": "无用药数据"}

    avg = sum(adherence_values) / len(adherence_values)
    latest = adherence_values[0]

    return {
        "status": "analyzed",
        "average_pct": round(avg, 1),
        "latest_pct": round(latest, 1),
        "trend": "improving" if len(adherence_values) >= 2 and adherence_values[0] > adherence_values[-1]
                 else "declining" if len(adherence_values) >= 2 and adherence_values[0] < adherence_values[-1]
                 else "stable",
        "weeks_tracked": len(adherence_values),
    }


def analyze_activity_trend(health_logs: list[dict], behavior_patterns: list[dict]) -> dict:
    """分析运动趋势"""
    step_readings = [
        log for log in health_logs
        if log.get("steps") is not None
    ]
    if not step_readings:
        avg_steps = None
        if behavior_patterns:
            avg_steps = behavior_patterns[0].get("avg_daily_steps")
        if avg_steps is None:
            return {"status": "no_data", "summary": "无运动数据"}
        return {
            "status": "partial",
            "avg_daily_steps": avg_steps,
            "data_source": "behavior_pattern",
        }

    steps_values = [r["steps"] for r in step_readings]
    avg_steps = sum(steps_values) / len(steps_values)
    goal_met_days = sum(1 for s in steps_values if s >= settings.DEFAULT_DAILY_STEPS_GOAL)

    return {
        "status": "analyzed",
        "avg_daily_steps": round(avg_steps),
        "max_steps": max(steps_values),
        "min_steps": min(steps_values),
        "goal_met_days": goal_met_days,
        "total_days": len(steps_values),
        "goal_met_pct": round(goal_met_days / len(steps_values) * 100, 1),
    }


def analyze_task_completion(task_data: dict) -> dict:
    """分析任务完成率"""
    total = task_data.get("total_tasks", 0)
    completed = task_data.get("completed_tasks", 0)
    if total == 0:
        return {"status": "no_data", "summary": "无任务数据"}

    return {
        "status": "analyzed",
        "total_tasks": total,
        "completed_tasks": completed,
        "completion_rate": round(completed / total * 100, 1),
        "streak_days": task_data.get("streak_days", 0),
    }


def generate_full_trend_analysis(
    health_logs: list[dict],
    behavior_patterns: list[dict],
    task_data: dict,
) -> dict:
    """生成完整趋势分析"""
    completeness = {}
    glucose = analyze_glucose_trend(health_logs)
    completeness["glucose"] = glucose["status"] != "no_data"

    egfr = analyze_egfr_trend(health_logs)
    completeness["egfr"] = egfr["status"] != "no_data"

    medication = analyze_medication_adherence(behavior_patterns)
    completeness["medication"] = medication["status"] != "no_data"

    activity = analyze_activity_trend(health_logs, behavior_patterns)
    completeness["activity"] = activity["status"] != "no_data"

    tasks = analyze_task_completion(task_data)
    completeness["tasks"] = tasks["status"] != "no_data"

    all_complete = all(completeness.values())

    return {
        "glucose_trend": glucose,
        "egfr_trend": egfr,
        "medication_adherence": medication,
        "activity_trend": activity,
        "task_completion": tasks,
        "data_completeness": completeness,
        "is_complete": all_complete,
    }
