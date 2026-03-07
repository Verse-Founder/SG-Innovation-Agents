"""
nodes/risk_assessment.py
风险评估节点：调用智能引擎 + 肾功能监测 + 复诊调度
"""
from state.task_state import TaskAgentState
from schemas.health import HealthSnapshot, BehaviorPattern
from engine.intelligence import analyze_and_generate_tasks
from engine.renal_monitor import assess_renal_status
from engine.checkup_scheduler import assess_checkup_needs


def risk_assessment_node(state: TaskAgentState) -> dict:
    """
    综合风险评估：
    1. AI 医学顾问分析（智能引擎）
    2. 肾功能专项评估
    3. 复诊需求评估
    """
    snapshot_data = state.get("health_snapshot", {})
    behavior_data = state.get("behavior_pattern", {})
    chat_insights = state.get("chat_insights", [])

    snapshot = HealthSnapshot(**snapshot_data) if snapshot_data else HealthSnapshot(user_id="unknown")
    behavior = BehaviorPattern(**behavior_data) if behavior_data else BehaviorPattern(user_id="unknown")

    # 1. AI 医学顾问分析
    risk_assessment, ai_tasks = analyze_and_generate_tasks(
        snapshot, behavior, chat_insights
    )

    # 2. 肾功能专项
    renal_result = assess_renal_status(snapshot)
    if renal_result["concern_level"] in ("warning", "critical"):
        risk_assessment.renal_concern = True
        for rec in renal_result["recommendations"]:
            if rec not in risk_assessment.recommended_actions:
                risk_assessment.recommended_actions.append(rec)

    # 3. 复诊需求
    checkup_recs = assess_checkup_needs(snapshot)
    for cr in checkup_recs:
        # 转换为任务格式
        ai_tasks.append({
            "category": "checkup",
            "title": cr["type"],
            "description": cr["reason"],
            "caring_message": cr["caring_message"],
            "priority": "critical" if cr["urgency"] == "critical" else "high" if cr["urgency"] == "high" else "medium",
            "points": 15 if cr["urgency"] == "critical" else 10,
        })

    print(f"[RiskAssessment] 综合风险: {risk_assessment.risk_level} | "
          f"肾功能关注: {renal_result['concern_level']} | "
          f"复诊建议: {len(checkup_recs)} 项 | 总任务: {len(ai_tasks)}")

    return {
        "risk_assessment": risk_assessment.model_dump(),
        "generated_tasks": ai_tasks,
        "llm_analysis": f"Risk: {risk_assessment.risk_level}, Tasks: {len(ai_tasks)}",
    }
