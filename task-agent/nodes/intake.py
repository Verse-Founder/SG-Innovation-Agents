"""
nodes/intake.py
触发信号接收节点：标准化来自不同源的触发数据
"""
from state.task_state import TaskAgentState


def intake_node(state: TaskAgentState) -> dict:
    """
    接收触发信号，标准化 payload
    支持的触发源：cron / chatbot / alert_agent / doctor / system
    """
    source = state.get("trigger_source", "system")
    payload = state.get("trigger_payload", {})

    print(f"[Intake] 触发源: {source} | payload keys: {list(payload.keys())}")

    # 标准化 payload
    normalized = {
        "source": source,
        "user_id": state.get("user_id", payload.get("user_id", "")),
        "request_type": payload.get("type", "general"),
        "request_text": payload.get("request", payload.get("text", "")),
        "alert_level": payload.get("severity", payload.get("alert_level", "none")),
        "raw": payload,
    }

    return {
        "trigger_payload": normalized,
        "user_id": normalized["user_id"],
        "error": None,
    }
