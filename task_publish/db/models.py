from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, Index, Numeric, JSON, SmallInteger
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

def _now() -> datetime:
    return datetime.utcnow()

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language_pref: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")

class QuizBank(Base):
    __tablename__ = "quiz_bank"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str] = mapped_column(String(300), nullable=False)
    option_b: Mapped[str] = mapped_column(String(300), nullable=False)
    option_c: Mapped[str] = mapped_column(String(300), nullable=False)
    option_d: Mapped[str] = mapped_column(String(300), nullable=False)
    correct_option: Mapped[str] = mapped_column(String(1), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

class RoutineTaskLog(Base):
    __tablename__ = "routine_task_log"

    task_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(30), nullable=False)
    task_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reward_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("idx_routine_user_type_period", "user_id", "task_type", "period", unique=True),
        Index("idx_routine_expires", "expires_at", "task_status"),
    )

class DynamicTaskLog(Base):
    __tablename__ = "dynamic_task_log"

    task_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), nullable=False)
    task_content: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    task_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    target_lat: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    target_lng: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reward_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("idx_dynamic_user_status", "user_id", "task_status"),
        Index("idx_dynamic_expires", "expires_at", "task_status"),
        Index("idx_dynamic_user_date", "user_id", "created_at"),
    )

class DynamicTaskRule(Base):
    __tablename__ = "dynamic_task_rule"

    rule_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.user_id"), nullable=True, unique=True)
    base_calorie: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    trigger_threshold: Mapped[float] = mapped_column(Numeric(4, 3), default=0.600, nullable=False)
    meal_pts: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    quiz_base_pts: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    quiz_bonus_pts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    weekly_pts: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    exercise_pts: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    is_active: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

class RewardLog(Base):
    __tablename__ = "reward_log"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), primary_key=True)
    total_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accumulated_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consumed_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

class UserFoodLog(Base):
    __tablename__ = "user_food_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    food_name: Mapped[str] = mapped_column(String(100), default="unknown", nullable=False)
    meal_type: Mapped[str] = mapped_column(String(10), nullable=False)
    gi_level: Mapped[str] = mapped_column(String(6), default="medium", nullable=False)
    total_calories: Mapped[float] = mapped_column(Numeric(6, 1), default=0, nullable=False)

    __table_args__ = (
        Index("idx_food_user_time", "user_id", "recorded_at"),
    )

# Mocks for foreign queries described in Section 10
class UserExerciseLog(Base):
    __tablename__ = "user_exercise_log"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    exercise_type: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    calories_burned: Mapped[float] = mapped_column(Float, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class UserCgmLog(Base):
    __tablename__ = "user_cgm_log"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    glucose: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class UserKnownPlaces(Base):
    __tablename__ = "user_known_places"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    place_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gps_lat: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    gps_lng: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
