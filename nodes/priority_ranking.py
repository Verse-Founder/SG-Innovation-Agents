"""
nodes/priority_ranking.py
优先级排序节点：排序 + 去重
"""
from state.task_state import TaskAgentState


PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def priority_ranking_node(state: TaskAgentState) -> dict:
    """
    按优先级排序任务，并去除重复
    排序规则：critical > high > medium > low
    """
    tasks = state.get("generated_tasks", []) or []

    # 去重（按 title 去重）
    seen_titles = set()
    unique_tasks = []
    for task in tasks:
        title = task.get("title", "")
        if title not in seen_titles:
            seen_titles.add(title)
            unique_tasks.append(task)

    # 按优先级排序
    sorted_tasks = sorted(
        unique_tasks,
        key=lambda t: PRIORITY_ORDER.get(t.get("priority", "low"), 3)
    )

    print(f"[Ranking] 去重: {len(tasks)} → {len(unique_tasks)} | 排序完成")
    return {"prioritized_tasks": sorted_tasks}
