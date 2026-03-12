"""
nodes/context_enrichment.py
上下文丰富：从用户档案、健康记录、行为历史、聊天记录中提取上下文
"""
from state.task_state import TaskAgentState
from utils.mock_data import (
    get_mock_user_profile, get_mock_health_snapshot,
    get_mock_behavior_pattern, get_mock_chat_insights,
)


from sqlalchemy.ext.asyncio import AsyncSession
from db.session import async_session_factory
from db.crud import get_user_profile, get_latest_metrics, get_latest_behavior_pattern

async def context_enrichment_node(state: TaskAgentState) -> dict:
    """
    丰富用户上下文
    """
    user_id = state.get("user_id", "user_001")
    trigger = state.get("trigger_payload", {})

    # 确定场景
    scenario = "normal"
    alert_level = trigger.get("alert_level", "none") if isinstance(trigger, dict) else "none"
    request_text = trigger.get("request_text", "") if isinstance(trigger, dict) else ""

    if alert_level in ("high", "critical"):
        scenario = "high_glucose"
    elif "运动" in request_text or "跑步" in request_text:
        scenario = "pre_exercise_risk"
    elif "肾" in request_text or "泡沫尿" in request_text:
        scenario = "renal_concern"

    # 获取数据（从数据库获取真实数据）
    async with async_session_factory() as session:
        profile_record = await get_user_profile(session, user_id)
        metrics_record = await get_latest_metrics(session, user_id)
        behavior_record = await get_latest_behavior_pattern(session, user_id)
        
        # 转换为字典，排除 SQLAlchemy 内部状态
        def to_dict(obj):
            if not obj: return None
            data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
            # 特殊处理：将数据库中的 calories 映射到 schemas 中的 today_calories
            if "calories" in data:
                data["today_calories"] = data.get("calories", 0.0)
            return data

        profile = to_dict(profile_record) if profile_record else get_mock_user_profile(user_id)
        snapshot = get_mock_health_snapshot(user_id, scenario=scenario)
        
        # 将真实指标注入快照
        if metrics_record:
            snapshot.weight_kg = metrics_record.weight
            snapshot.height_cm = profile.get("height")
            
        behavior = to_dict(behavior_record) if behavior_record else get_mock_behavior_pattern(user_id)
        if hasattr(behavior, "model_dump"): # if it's still a mock/pydantic
            behavior = behavior.model_dump()
            
        chat_insights = get_mock_chat_insights()

    # 如果触发来源有聊天内容，追加
    if request_text:
        chat_insights.append(f"用户最新消息：{request_text}")

    print(f"[Context] 场景: {scenario} | 血糖趋势: {snapshot.glucose.trend} | "
          f"eGFR: {snapshot.renal.egfr} | 聊天摘要: {len(chat_insights)} 条")

    return {
        "user_profile": profile,
        "health_snapshot": snapshot.model_dump(),
        "behavior_pattern": behavior,
        "chat_insights": chat_insights,
    }
