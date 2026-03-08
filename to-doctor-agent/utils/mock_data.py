"""
utils/mock_data.py
Mock 数据 — 模拟患者健康数据（测试/开发用）
"""
import random
from datetime import datetime, timedelta


def get_mock_health_logs(user_id: str, days: int = 30) -> list[dict]:
    """生成 mock 健康数据"""
    logs = []
    now = datetime.utcnow()
    for i in range(days):
        date = now - timedelta(days=days - i - 1)
        # 血糖记录
        logs.append({
            "user_id": user_id,
            "blood_glucose": round(random.uniform(4.5, 12.0), 1),
            "glucose_context": random.choice(["fasting", "postprandial", "random"]),
            "steps": random.randint(2000, 10000),
            "heart_rate": random.randint(60, 100),
            "egfr": round(random.uniform(50, 120), 1) if i % 7 == 0 else None,
            "created_at": date.isoformat(),
        })
    return logs


def get_mock_behavior_patterns(user_id: str) -> list[dict]:
    """生成 mock 行为模式数据"""
    return [
        {
            "user_id": user_id,
            "avg_daily_steps": random.randint(4000, 8000),
            "medication_adherence_pct": round(random.uniform(60, 100), 1),
            "task_completion_rate": round(random.uniform(0.5, 1.0), 2),
            "glucose_control_score": round(random.uniform(50, 95), 1),
            "week_number": i,
        }
        for i in range(4)
    ]


def get_mock_task_data(user_id: str) -> dict:
    """生成 mock 任务数据"""
    total = random.randint(20, 50)
    completed = random.randint(int(total * 0.5), total)
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "streak_days": random.randint(0, 14),
    }
