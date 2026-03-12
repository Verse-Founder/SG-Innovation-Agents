"""
engine/points_engine.py
积分计算引擎
"""
from schemas.points import PointsTransaction, PointsBalance
from config import settings
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from db.crud import get_latest_behavior_pattern, create_behavior_pattern


def calculate_task_points(
    task_category: str,
    task_type: str,
    streak_days: int | PointsBalance = 0,
) -> int:
    """计算任务完成积分，包含连击加成"""
    # 如果传入的是 PointsBalance 对象，提取 streak_days
    if isinstance(streak_days, PointsBalance):
        streak_days = streak_days.streak_days

    base_points = {
        "exercise": settings.POINTS_DAILY_EXERCISE,
        "diet": settings.POINTS_MEAL_PHOTO,
        "medication": settings.POINTS_MEDICATION_ON_TIME,
        "quiz": settings.POINTS_DAILY_QUIZ,
        "monitoring": 5,
        "checkup": 15,
        "renal": 10,
    }

    points = base_points.get(task_category, 5)

    # 1. 类型加成
    if task_type == "weekly_personalized":
        points += settings.POINTS_WEEKLY_BONUS

    # 2. 连续完成乘数 (Streak Multiplier)
    # 规则：每连续一天增加 10% (0.1)，上限 2.0x
    multiplier = 1.0 + (streak_days * 0.1)
    if multiplier > 2.0:
        multiplier = 2.0
    
    final_points = int(points * multiplier)
    return final_points


async def reset_streak(session: AsyncSession, user_id: str):
    """重置用户连击数"""
    pattern = await get_latest_behavior_pattern(session, user_id)
    now = datetime.now(timezone.utc)
    
    if pattern:
        pattern.current_streak_days = 0
        pattern.last_streak_reset = now
    else:
        # 如果没有记录，创建一个初始化的记录
        await create_behavior_pattern(
            session,
            user_id=user_id,
            current_streak_days=0,
            last_streak_reset=now
        )
    await session.flush()


def calculate_daily_bonus(meal_count: int, photo_count: int = 0) -> int:
    """
    每日奖励：
    - 完成 3 餐记录 -> 额外奖励 5 积分
    - 每上传一张食物照片 -> 额外 2 积分
    """
    bonus = 0
    if meal_count >= 3:
        bonus += 5
    bonus += photo_count * 2
    return bonus


def process_task_completion(
    user_id: str,
    task_id: str,
    task_category: str,
    task_type: str,
    current_balance: PointsBalance,
) -> tuple[PointsTransaction, PointsBalance]:
    """处理任务完成，返回交易记录和更新后的余额"""
    points = calculate_task_points(task_category, task_type, current_balance.streak_days)

    transaction = PointsTransaction(
        user_id=user_id,
        amount=points,
        reason=f"完成任务: {task_category} (连击 {current_balance.streak_days} 天)",
        task_id=task_id,
        transaction_type="earn",
    )

    # 更新余额对象
    new_balance = current_balance.model_copy()
    new_balance.total_earned += points
    new_balance.current_balance += points
    new_balance.streak_days += 1
    
    return transaction, new_balance


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
