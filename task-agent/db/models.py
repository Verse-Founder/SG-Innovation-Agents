"""
db/models.py
SQLAlchemy 2.0 声明式 ORM 模型
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime, JSON,
    ForeignKey, Index,
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column,
)


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(32), nullable=False, default="daily_routine")
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="monitoring")
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    caring_message: Mapped[str] = mapped_column(Text, default="")
    points: Mapped[int] = mapped_column(Integer, default=5)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)
    trigger_source: Mapped[str] = mapped_column(String(32), default="system")

    __table_args__ = (
        Index("ix_tasks_user_status", "user_id", "status"),
    )


class UserHealthLog(Base):
    __tablename__ = "user_health_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    blood_glucose: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    glucose_context: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    egfr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    proteinuria: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hba1c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    heart_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    blood_pressure_sys: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    blood_pressure_dia: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    calories: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_health_user_time", "user_id", "recorded_at"),
    )


class TaskCompletion(Base):
    __tablename__ = "task_completions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    points_earned: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PointsLedger(Base):
    __tablename__ = "points_ledger"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(256), default="")
    task_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(16), default="earn")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class BehaviorPatternRecord(Base):
    __tablename__ = "behavior_patterns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    week_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    avg_daily_calories: Mapped[float] = mapped_column(Float, default=0.0)
    exercise_days_per_week: Mapped[int] = mapped_column(Integer, default=0)
    exercise_preferred_time: Mapped[str] = mapped_column(String(16), default="afternoon")
    meal_regularity_score: Mapped[float] = mapped_column(Float, default=0.0)
    medication_adherence_pct: Mapped[float] = mapped_column(Float, default=100.0)
    task_completion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    glucose_control_score: Mapped[float] = mapped_column(Float, default=0.0)
    current_streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_streak_reset: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ChatInsight(Base):
    __tablename__ = "chat_insights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    insight_type: Mapped[str] = mapped_column(String(32), default="general")
    content: Mapped[str] = mapped_column(Text, default="")
    source_message_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # cm
    gender: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    birth_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class UserMetricsLog(Base):
    __tablename__ = "user_metrics_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # kg
    waist_circumference: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # cm
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

