"""
graph/builder.py
LangGraph 报告生成流水线
START → data_collector → trend_analysis → risk_summary → recommendation → report_formatter → END
"""
import logging
from langgraph.graph import StateGraph, START, END
from state.report_state import ReportState
from engine.trend_analyzer import generate_full_trend_analysis
from engine.report_generator import generate_report_data, generate_report_summary
from engine.appointment_advisor import generate_appointment_suggestions
from utils.llm_factory import call_sealion

logger = logging.getLogger(__name__)


# ── 节点 ─────────────────────────────────────────────────

def data_collector(state: ReportState) -> ReportState:
    """从 mock 数据源收集患者数据（实际部署时从共享 DB 读取）"""
    from utils.mock_data import get_mock_health_logs, get_mock_behavior_patterns, get_mock_task_data

    user_id = state["user_id"]
    errors = []

    try:
        health_logs = get_mock_health_logs(user_id)
    except Exception as e:
        health_logs = []
        errors.append(f"健康数据读取失败: {e}")

    try:
        behavior_patterns = get_mock_behavior_patterns(user_id)
    except Exception as e:
        behavior_patterns = []
        errors.append(f"行为数据读取失败: {e}")

    try:
        task_data = get_mock_task_data(user_id)
    except Exception as e:
        task_data = {}
        errors.append(f"任务数据读取失败: {e}")

    return {
        **state,
        "health_logs": health_logs,
        "behavior_patterns": behavior_patterns,
        "task_data": task_data,
        "prescriptions": [],
        "user_profile": {"patient_id": user_id},
        "errors": errors,
    }


def trend_analysis(state: ReportState) -> ReportState:
    """运行趋势分析"""
    analysis = generate_full_trend_analysis(
        health_logs=state.get("health_logs", []),
        behavior_patterns=state.get("behavior_patterns", []),
        task_data=state.get("task_data", {}),
    )
    return {
        **state,
        "trend_analysis": analysis,
        "data_completeness": analysis["data_completeness"],
    }


def risk_summary(state: ReportState) -> ReportState:
    """使用 LLM 生成风险摘要（失败时回退到规则型摘要）"""
    analysis = state.get("trend_analysis", {})

    prompt = f"""你是一位资深的新加坡糖尿病专科护理顾问。请根据以下患者健康趋势分析，
生成一份简洁的风险评估摘要（不超过 200 字）。

血糖趋势: {analysis.get('glucose_trend', {})}
肾功能: {analysis.get('egfr_trend', {})}
用药依从性: {analysis.get('medication_adherence', {})}
运动: {analysis.get('activity_trend', {})}
任务完成率: {analysis.get('task_completion', {})}

请用中文回复，包含：1.总体风险级别 2.主要关注点 3.建议行动"""

    try:
        summary_text = call_sealion(prompt)
        if not summary_text.strip():
            raise ValueError("LLM 返回空结果")
    except Exception as e:
        logger.warning(f"[Graph] LLM 摘要生成失败: {e}, 使用规则型回退")
        summary_text = ""

    return {**state, "risk_summary": summary_text}


def recommendation(state: ReportState) -> ReportState:
    """生成预约建议"""
    analysis = state.get("trend_analysis", {})
    suggestions = generate_appointment_suggestions(analysis)
    return {**state, "appointment_suggestions": suggestions}


def report_formatter(state: ReportState) -> ReportState:
    """组装最终报告"""
    report_data = generate_report_data(
        user_id=state["user_id"],
        health_logs=state.get("health_logs", []),
        behavior_patterns=state.get("behavior_patterns", []),
        task_data=state.get("task_data", {}),
        prescriptions=state.get("prescriptions", []),
        user_profile=state.get("user_profile"),
    )

    # 添加 LLM 风险摘要
    llm_summary = state.get("risk_summary", "")
    if llm_summary:
        report_data["ai_risk_summary"] = llm_summary

    # 生成文字摘要
    summary = generate_report_summary(report_data)

    # PDF 生成（如果 ReportLab 可用）
    pdf_path = ""
    try:
        from pdf.generator import generate_pdf_report
        pdf_path = generate_pdf_report(report_data)
    except Exception as e:
        logger.warning(f"[Graph] PDF 生成跳过: {e}")
        state.get("errors", []).append(f"PDF 生成失败: {e}")

    return {
        **state,
        "report_data": report_data,
        "summary": summary,
        "pdf_path": pdf_path,
    }


# ── 构建图 ───────────────────────────────────────────────

def build_report_graph() -> StateGraph:
    """构建报告生成 LangGraph"""
    graph = StateGraph(ReportState)

    graph.add_node("data_collector", data_collector)
    graph.add_node("trend_analysis", trend_analysis)
    graph.add_node("risk_summary", risk_summary)
    graph.add_node("recommendation", recommendation)
    graph.add_node("report_formatter", report_formatter)

    graph.add_edge(START, "data_collector")
    graph.add_edge("data_collector", "trend_analysis")
    graph.add_edge("trend_analysis", "risk_summary")
    graph.add_edge("risk_summary", "recommendation")
    graph.add_edge("recommendation", "report_formatter")
    graph.add_edge("report_formatter", END)

    return graph.compile()


def run_report_pipeline(user_id: str, days: int = 30) -> dict:
    """运行报告生成流水线"""
    graph = build_report_graph()
    result = graph.invoke({
        "user_id": user_id,
        "days": days,
        "errors": [],
    })
    return {
        "report_data": result.get("report_data", {}),
        "summary": result.get("summary", ""),
        "pdf_path": result.get("pdf_path", ""),
        "appointment_suggestions": result.get("appointment_suggestions", []),
        "data_completeness": result.get("data_completeness", {}),
        "errors": result.get("errors", []),
    }
