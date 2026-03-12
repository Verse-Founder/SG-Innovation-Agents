"""
db/crud.py
数据库 CRUD 操作封装
"""
import json
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    Task, UserHealthLog, TaskCompletion,
    PointsLedger, BehaviorPatternRecord, ChatInsight,
    UserProfile, UserMetricsLog,
)


# ── 任务 CRUD ────────────────────────────────────────────

async def create_task(
    session: AsyncSession,
    *,
    user_id: str,
    task_type: str = "daily_routine",
    category: str = "monitoring",
    title: str,
    description: str = "",
    caring_message: str = "",
    points: int = 5,
    priority: str = "medium",
    status: str = "pending",
    deadline: Optional[datetime] = None,
    trigger_source: str = "system",
    metadata: Optional[dict] = None,
) -> Task:
    task = Task(
        id=str(uuid.uuid4()),
        user_id=user_id,
        task_type=task_type,
        category=category,
        title=title,
        description=description,
        caring_message=caring_message,
        points=points,
        priority=priority,
        status=status,
        deadline=deadline,
        trigger_source=trigger_source,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    session.add(task)
    await session.flush()
    return task


async def get_user_tasks(
    session: AsyncSession,
    user_id: str,
    status: Optional[str] = None,
    limit: int = 50,
) -> list[Task]:
    stmt = select(Task).where(Task.user_id == user_id)
    if status:
        stmt = stmt.where(Task.status == status)
    stmt = stmt.order_by(Task.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_task_by_id(session: AsyncSession, task_id: str) -> Optional[Task]:
    result = await session.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def complete_task(
    session: AsyncSession,
    task_id: str,
    user_id: str,
) -> Optional[TaskCompletion]:
    task = await get_task_by_id(session, task_id)
    if not task or task.user_id != user_id:
        return None

    now = datetime.utcnow()
    task.status = "completed"
    task.completed_at = now
    task.updated_at = now

    # 计算积分：考虑 Streak 加成
    from engine.points_engine import calculate_task_points
    pattern = await get_latest_behavior_pattern(session, user_id)
    streak = pattern.current_streak_days if pattern else 0
    
    actual_points = calculate_task_points(
        task_category=task.category,
        task_type=task.task_type,
        streak_days=streak
    )

    completion = TaskCompletion(
        id=str(uuid.uuid4()),
        user_id=user_id,
        task_id=task_id,
        completed_at=now,
        points_earned=actual_points,
    )
    session.add(completion)

    ledger = PointsLedger(
        id=str(uuid.uuid4()),
        user_id=user_id,
        amount=actual_points,
        reason=f"完成任务: {task.title} (连击 {streak} 天)",
        task_id=task_id,
        transaction_type="earn",
    )
    session.add(ledger)

    await session.flush()
    return completion


# ── 积分 CRUD ────────────────────────────────────────────

async def add_points_transaction(
    session: AsyncSession,
    *,
    user_id: str,
    amount: int,
    reason: str = "",
    task_id: Optional[str] = None,
    transaction_type: str = "earn",
) -> PointsLedger:
    entry = PointsLedger(
        id=str(uuid.uuid4()),
        user_id=user_id,
        amount=amount,
        reason=reason,
        task_id=task_id,
        transaction_type=transaction_type,
    )
    session.add(entry)
    await session.flush()
    return entry


async def get_points_balance(session: AsyncSession, user_id: str) -> dict:
    earned_stmt = select(func.coalesce(func.sum(PointsLedger.amount), 0)).where(
        PointsLedger.user_id == user_id,
        PointsLedger.transaction_type.in_(["earn", "bonus"]),
    )
    earned_result = await session.execute(earned_stmt)
    total_earned = earned_result.scalar() or 0

    spent_stmt = select(func.coalesce(func.sum(PointsLedger.amount), 0)).where(
        PointsLedger.user_id == user_id,
        PointsLedger.transaction_type == "spend",
    )
    spent_result = await session.execute(spent_stmt)
    total_spent = spent_result.scalar() or 0

    return {
        "user_id": user_id,
        "total_earned": int(total_earned),
        "total_spent": int(total_spent),
        "current_balance": int(total_earned) - int(total_spent),
    }


# ── 健康数据 CRUD ────────────────────────────────────────

async def create_health_log(
    session: AsyncSession,
    *,
    user_id: str,
    blood_glucose: Optional[float] = None,
    glucose_context: Optional[str] = None,
    egfr: Optional[float] = None,
    proteinuria: Optional[float] = None,
    hba1c: Optional[float] = None,
    heart_rate: Optional[int] = None,
    blood_pressure_dia: Optional[int] = None,
    calories: Optional[float] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> UserHealthLog:
    log = UserHealthLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        blood_glucose=blood_glucose,
        glucose_context=glucose_context,
        egfr=egfr,
        proteinuria=proteinuria,
        hba1c=hba1c,
        blood_pressure_dia=blood_pressure_dia,
        calories=calories,
        latitude=latitude,
        longitude=longitude,
    )
    session.add(log)
    await session.flush()
    return log


async def get_recent_health_logs(
    session: AsyncSession,
    user_id: str,
    limit: int = 20,
) -> list[UserHealthLog]:
    stmt = (
        select(UserHealthLog)
        .where(UserHealthLog.user_id == user_id)
        .order_by(UserHealthLog.recorded_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ── 聊天洞察 CRUD ────────────────────────────────────────

async def create_chat_insight(
    session: AsyncSession,
    *,
    user_id: str,
    insight_type: str = "general",
    content: str = "",
    source_message_id: Optional[str] = None,
) -> ChatInsight:
    insight = ChatInsight(
        id=str(uuid.uuid4()),
        user_id=user_id,
        insight_type=insight_type,
        content=content,
        source_message_id=source_message_id,
    )
    session.add(insight)
    await session.flush()
    return insight


# ── 行为模式 CRUD ────────────────────────────────────────

async def create_behavior_pattern(
    session: AsyncSession,
    *,
    user_id: str,
    week_start: Optional[datetime] = None,
    avg_daily_calories: float = 0.0,
    exercise_days_per_week: int = 0,
    medication_adherence_pct: float = 100.0,
    task_completion_rate: float = 0.0,
    glucose_control_score: float = 0.0,
    current_streak_days: int = 0,
    last_streak_reset: Optional[datetime] = None,
) -> BehaviorPatternRecord:
    bp = BehaviorPatternRecord(
        id=str(uuid.uuid4()),
        user_id=user_id,
        week_start=week_start,
        avg_daily_calories=avg_daily_calories,
        exercise_days_per_week=exercise_days_per_week,
        medication_adherence_pct=medication_adherence_pct,
        task_completion_rate=task_completion_rate,
        glucose_control_score=glucose_control_score,
        current_streak_days=current_streak_days,
        last_streak_reset=last_streak_reset,
    )
    session.add(bp)
    await session.flush()
    return bp


async def get_latest_behavior_pattern(session: AsyncSession, user_id: str) -> Optional[BehaviorPatternRecord]:
    stmt = (
        select(BehaviorPatternRecord)
        .where(BehaviorPatternRecord.user_id == user_id)
        .order_by(BehaviorPatternRecord.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# ── 用户档案与指标 CRUD ────────────────────────────────────

async def upsert_user_profile(
    session: AsyncSession,
    *,
    user_id: str,
    height: Optional[float] = None,
    gender: Optional[str] = None,
    birth_date: Optional[datetime] = None,
    onboarding_completed: bool = False,
) -> UserProfile:
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(user_id=user_id)
        session.add(profile)

    if height is not None:
        profile.height = height
    if gender is not None:
        profile.gender = gender
    if birth_date is not None:
        profile.birth_date = birth_date
    profile.onboarding_completed = onboarding_completed

    await session.flush()
    return profile


async def get_user_profile(session: AsyncSession, user_id: str) -> Optional[UserProfile]:
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_metrics_log(
    session: AsyncSession,
    *,
    user_id: str,
    weight: Optional[float] = None,
    waist_circumference: Optional[float] = None,
) -> UserMetricsLog:
    log = UserMetricsLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        weight=weight,
        waist_circumference=waist_circumference,
    )
    session.add(log)
    await session.flush()
    return log


async def get_latest_metrics(session: AsyncSession, user_id: str) -> Optional[UserMetricsLog]:
    stmt = (
        select(UserMetricsLog)
        .where(UserMetricsLog.user_id == user_id)
        .order_by(UserMetricsLog.recorded_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
