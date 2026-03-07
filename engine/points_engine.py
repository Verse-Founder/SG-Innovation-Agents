"""
engine/points_engine.py
积分计算引擎
"""
from schemas.points import PointsTransaction, PointsBalance
from config import settings
from datetime import datetime


def calculate_task_points(
    task_category: str,
    task_type: str,
    streak_days: int = 0,
) -> int:
    """计算任务完成积分"""
    base_points = {
        "exercise": settings.POINTS_DAILY_STEPS,
        "diet": settings.POINTS_MEAL_PHOTO,
        "medication": settings.POINTS_MEDICATION_ON_TIME,
        "quiz": settings.POINTS_DAILY_QUIZ,
        "monitoring": 5,
        "checkup": 15,
        "renal": 10,
    }

    points = base_points.get(task_category, 5)

    # 周常任务额外奖励
    if task_type == "weekly_personalized":
        points += settings.POINTS_WEEKLY_BONUS

    # 连续完成乘数（3天以上）
    if streak_days >= 3:
        multiplier = min(settings.POINTS_STREAK_MULTIPLIER, 1.0 + streak_days * 0.1)
        points = int(points * multiplier)

    return points


def process_task_completion(
    user_id: str,
    task_id: str,
    task_category: str,
    task_type: str,
    current_balance: PointsBalance,
) -> tuple[PointsTransaction, PointsBalance]:
    """处理任务完成，计算积分并更新余额"""
    points = calculate_task_points(
        task_category, task_type, current_balance.streak_days
    )

    transaction = PointsTransaction(
        user_id=user_id,
        amount=points,
        reason=f"完成任务: {task_category}",
        task_id=task_id,
        transaction_type="earn",
    )

    updated_balance = PointsBalance(
        user_id=user_id,
        total_earned=current_balance.total_earned + points,
        total_spent=current_balance.total_spent,
        current_balance=current_balance.current_balance + points,
        streak_days=current_balance.streak_days + 1,
        streak_multiplier=min(settings.POINTS_STREAK_MULTIPLIER,
                              1.0 + (current_balance.streak_days + 1) * 0.1),
    )

    return transaction, updated_balance


def create_energy_steal_transaction(
    stealer_id: str,
    target_id: str,
    amount: int = 1,
) -> PointsTransaction:
    """创建偷能量交易（预留，需群组系统支撑）"""
    return PointsTransaction(
        user_id=stealer_id,
        amount=amount,
        reason=f"从 {target_id} 偷取能量",
        transaction_type="steal",
    )
