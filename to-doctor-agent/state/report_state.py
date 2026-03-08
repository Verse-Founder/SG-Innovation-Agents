"""
state/report_state.py
LangGraph 共享状态 — 报告生成流水线
"""
from typing import TypedDict, Optional


class ReportState(TypedDict, total=False):
    # 输入
    user_id: str
    report_id: str
    days: int

    # 数据收集
    health_logs: list[dict]
    behavior_patterns: list[dict]
    task_data: dict
    prescriptions: list[dict]
    user_profile: dict

    # 分析结果
    trend_analysis: dict
    risk_summary: str

    # 输出
    report_data: dict
    summary: str
    pdf_path: str
    appointment_suggestions: list[dict]

    # 容错
    data_completeness: dict
    errors: list[str]
