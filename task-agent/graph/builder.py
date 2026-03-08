"""
graph/builder.py
LangGraph 图定义：Task Agent 处理流水线

流程：
START → intake → context_enrichment → risk_assessment
      → task_generation → priority_ranking → output_formatter → END
"""
from langgraph.graph import StateGraph, END
from state.task_state import TaskAgentState
from nodes.intake import intake_node
from nodes.context_enrichment import context_enrichment_node
from nodes.risk_assessment import risk_assessment_node
from nodes.task_generation import task_generation_node
from nodes.priority_ranking import priority_ranking_node
from nodes.output_formatter import output_formatter_node


def build_task_agent_graph() -> StateGraph:
    """构建 Task Agent 的 LangGraph"""
    graph = StateGraph(TaskAgentState)

    # 添加节点
    graph.add_node("intake", intake_node)
    graph.add_node("context_enrichment", context_enrichment_node)
    graph.add_node("risk_assessment", risk_assessment_node)
    graph.add_node("task_generation", task_generation_node)
    graph.add_node("priority_ranking", priority_ranking_node)
    graph.add_node("output_formatter", output_formatter_node)

    # 定义边
    graph.set_entry_point("intake")
    graph.add_edge("intake", "context_enrichment")
    graph.add_edge("context_enrichment", "risk_assessment")
    graph.add_edge("risk_assessment", "task_generation")
    graph.add_edge("task_generation", "priority_ranking")
    graph.add_edge("priority_ranking", "output_formatter")
    graph.add_edge("output_formatter", END)

    return graph


def get_compiled_graph():
    """获取编译后的可执行图"""
    graph = build_task_agent_graph()
    return graph.compile()


def run_task_agent(
    user_id: str,
    trigger_source: str = "system",
    trigger_payload: dict | None = None,
    user_profile: dict | None = None,
) -> dict:
    """
    运行 Task Agent
    这是对外暴露的主入口函数

    Args:
        user_id: 用户 ID
        trigger_source: 触发源 (cron / chatbot / alert_agent / doctor / system)
        trigger_payload: 触发数据
        user_profile: 用户档案（可选，不传则从 mock 获取）

    Returns:
        输出 payload（包含 tasks batch, notifications, risk level 等）
    """
    app = get_compiled_graph()

    initial_state: TaskAgentState = {
        "trigger_source": trigger_source,
        "trigger_payload": trigger_payload or {},
        "user_id": user_id,
        "user_profile": user_profile or {},
        "health_snapshot": None,
        "behavior_pattern": None,
        "chat_insights": None,
        "risk_assessment": None,
        "llm_analysis": None,
        "generated_tasks": None,
        "prioritized_tasks": None,
        "output_payload": None,
        "points_delta": None,
        "error": None,
    }

    print(f"\n{'='*60}")
    print(f"🚀 Task Agent 启动 | 用户: {user_id} | 触发: {trigger_source}")
    print(f"{'='*60}")

    result = app.invoke(initial_state)

    output = result.get("output_payload", {})
    if output:
        batch = output.get("batch", {})
        tasks = batch.get("tasks", [])
        print(f"\n{'='*60}")
        print(f"✅ 完成 | 生成 {len(tasks)} 个任务 | 风险: {output.get('risk_level', 'low')}")
        print(f"{'='*60}\n")

    return output
