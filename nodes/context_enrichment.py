"""
nodes/context_enrichment.py
上下文丰富：从用户档案、健康记录、行为历史、聊天记录中提取上下文
"""
from state.task_state import TaskAgentState
from utils.mock_data import (
    get_mock_user_profile, get_mock_health_snapshot,
    get_mock_behavior_pattern, get_mock_chat_insights,
)


def context_enrichment_node(state: TaskAgentState) -> dict:
    """
    丰富用户上下文

    数据来源：
    1. 用户档案 (medications, conditions, preferences)
    2. 健康记录 (CGM 血糖, 心率, 步数, eGFR)
    3. 行为历史 (运动习惯, 用餐规律, 服药模式)
    4. 聊天记录摘要 (食物, 情绪, 问询, 症状)
    """
    user_id = state.get("user_id", "user_001")
    trigger = state.get("trigger_payload", {})

    # 确定场景
    scenario = "normal"
    alert_level = trigger.get("alert_level", "none") if isinstance(trigger, dict) else "none"
    request_text = trigger.get("request_text", "") if isinstance(trigger, dict) else ""

    if alert_level in ("high", "critical"):
        scenario = "high_glucose"  # 预警触发
    elif "运动" in request_text or "跑步" in request_text:
        scenario = "pre_exercise_risk"
    elif "肾" in request_text or "泡沫尿" in request_text:
        scenario = "renal_concern"

    # 获取数据（目前使用 mock，后续接 MySQL）
    profile = state.get("user_profile") or get_mock_user_profile(user_id)
    snapshot = get_mock_health_snapshot(user_id, scenario=scenario)
    behavior = get_mock_behavior_pattern(user_id)
    chat_insights = get_mock_chat_insights()

    # 如果触发来源有聊天内容，追加
    if request_text:
        chat_insights.append(f"用户最新消息：{request_text}")

    print(f"[Context] 场景: {scenario} | 血糖趋势: {snapshot.glucose.trend} | "
          f"eGFR: {snapshot.renal.egfr} | 聊天摘要: {len(chat_insights)} 条")

    return {
        "user_profile": profile,
        "health_snapshot": snapshot.model_dump(),
        "behavior_pattern": behavior.model_dump(),
        "chat_insights": chat_insights,
    }
