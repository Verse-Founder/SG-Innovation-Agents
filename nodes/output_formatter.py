"""
nodes/output_formatter.py
输出格式化节点：生成前端可消费的 JSON payload + 推送通知
"""
import uuid
from datetime import datetime, timedelta
from state.task_state import TaskAgentState
from schemas.task import TaskResponse, TaskBatch, TaskType, TaskCategory, TaskPriority, TaskStatus
from utils.time_utils import now_sgt


def output_formatter_node(state: TaskAgentState) -> dict:
    """
    将排序后的任务列表转换为标准化前端 JSON
    """
    tasks_raw = state.get("prioritized_tasks", []) or []
    user_id = state.get("user_id", "unknown")
    risk = state.get("risk_assessment", {}) or {}

    task_responses = []
    for t in tasks_raw:
        try:
            category = t.get("category", "monitoring")
            priority = t.get("priority", "medium")
            task_type = _infer_task_type(t, state.get("trigger_source", "system"))

            task_resp = TaskResponse(
                task_id=str(uuid.uuid4())[:8],
                user_id=user_id,
                task_type=TaskType(task_type),
                category=TaskCategory(category) if category in TaskCategory.__members__.values() else TaskCategory.MONITORING,
                title=t.get("title", "健康任务"),
                description=t.get("description", ""),
                caring_message=t.get("caring_message", ""),
                points=t.get("points", 5),
                priority=TaskPriority(priority) if priority in TaskPriority.__members__.values() else TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                deadline=now_sgt() + timedelta(hours=24),
                created_at=now_sgt(),
            )
            task_responses.append(task_resp)
        except Exception as e:
            print(f"[OutputFormatter] 格式化任务失败: {e} | raw: {t}")

    # 组装批次
    batch = TaskBatch(
        user_id=user_id,
        batch_type="dynamic",
        tasks=task_responses,
        generated_at=now_sgt(),
        summary=_generate_summary(task_responses, risk),
    )

    # 推送通知
    notifications = _build_notifications(task_responses, risk)

    output = {
        "batch": batch.model_dump(mode="json"),
        "notifications": notifications,
        "risk_level": risk.get("risk_level", "low"),
        "requires_doctor_review": risk.get("requires_doctor_review", False),
        "renal_concern": risk.get("renal_concern", False),
    }

    print(f"[OutputFormatter] 输出 {len(task_responses)} 个任务 | "
          f"风险: {output['risk_level']} | 通知: {len(notifications)} 条")

    return {"output_payload": output}


def _infer_task_type(task: dict, trigger_source: str) -> str:
    """根据触发源推断任务类型"""
    if trigger_source == "cron":
        return "daily_routine"
    elif trigger_source == "doctor":
        return "doctor_assigned"
    elif task.get("priority") in ("critical", "high"):
        return "dynamic_risk"
    else:
        return "weekly_personalized"


def _generate_summary(tasks: list, risk: dict) -> str:
    """生成批次总结语"""
    if not tasks:
        return "今天状态不错，继续保持！💚"

    risk_level = risk.get("risk_level", "low")
    n = len(tasks)

    if risk_level == "critical":
        return f"⚠️ 有 {n} 个重要事项需要您关注，请优先处理。"
    elif risk_level == "high":
        return f"💛 为您准备了 {n} 个任务，有些需要尽快处理哦。"
    else:
        return f"🌿 今天有 {n} 个小任务等着您，慢慢来不着急。"


def _build_notifications(tasks: list, risk: dict) -> list[dict]:
    """构建推送通知"""
    notifications = []

    # 高优先级任务立即通知
    critical_tasks = [t for t in tasks if t.priority == TaskPriority.CRITICAL]
    for task in critical_tasks:
        notifications.append({
            "type": "push",
            "title": f"⚠️ {task.title}",
            "body": task.caring_message or task.description,
            "priority": "high",
            "action_url": f"/tasks/{task.task_id}",
        })

    # 普通任务汇总通知
    normal_count = len(tasks) - len(critical_tasks)
    if normal_count > 0:
        notifications.append({
            "type": "push",
            "title": f"🌿 今天有 {normal_count} 个健康小任务",
            "body": "打开看看今天的计划吧！",
            "priority": "normal",
            "action_url": "/tasks",
        })

    return notifications
