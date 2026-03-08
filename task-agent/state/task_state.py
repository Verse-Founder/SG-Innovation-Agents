"""
state/task_state.py
LangGraph 共享状态定义
"""
from typing import Optional
from typing_extensions import TypedDict


class TaskAgentState(TypedDict):
    # ── 触发信号 ─────────────────────────────────────────
    trigger_source: str           # cron / chatbot / alert_agent / doctor / system
    trigger_payload: dict         # 原始触发数据

    # ── 用户信息 ─────────────────────────────────────────
    user_id: str
    user_profile: dict            # 用户档案

    # ── 健康上下文 ───────────────────────────────────────
    health_snapshot: Optional[dict]    # HealthSnapshot 序列化
    behavior_pattern: Optional[dict]   # BehaviorPattern 序列化
    chat_insights: Optional[list]      # 聊天记录摘要列表

    # ── 智能分析结果 ─────────────────────────────────────
    risk_assessment: Optional[dict]    # RiskAssessment 序列化
    llm_analysis: Optional[str]        # LLM 原始分析文本

    # ── 任务生成 ─────────────────────────────────────────
    generated_tasks: Optional[list]    # 生成的任务列表
    prioritized_tasks: Optional[list]  # 排序后的任务列表

    # ── 输出 ─────────────────────────────────────────────
    output_payload: Optional[dict]     # 前端 JSON payload
    points_delta: Optional[list]       # 积分变动列表

    # ── 错误 ─────────────────────────────────────────────
    error: Optional[str]
