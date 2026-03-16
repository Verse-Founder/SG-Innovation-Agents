from datetime import datetime, date, time
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime, Date, Time,
    ForeignKey, Index, Numeric, JSON, SmallInteger, Enum as SQLEnum, BigInteger, func, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

def _now() -> datetime:
    return datetime.utcnow()

# ─────────────────────────────────────────
# User profile 
# ─────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    birth_year: Mapped[Optional[int]] = mapped_column(Integer)
    gender: Mapped[Optional[str]] = mapped_column(String(10)) # SQLEnum issues with sqlite sometimes, string is safe
    waist_cm: Mapped[Optional[float]] = mapped_column(Numeric(5, 1))
    weight_kg: Mapped[Optional[float]] = mapped_column(Numeric(5, 1))
    height_cm: Mapped[Optional[float]] = mapped_column(Numeric(5, 1))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    @property
    def bmi(self) -> float:
        if self.weight_kg and self.height_cm and self.height_cm > 0:
            return float(self.weight_kg) / ((float(self.height_cm) / 100) ** 2)
        return 0.0

# ─────────────────────────────────────────
# CGM blood glucose log
# ─────────────────────────────────────────
class UserCgmLog(Base):
    __tablename__ = "user_cgm_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    glucose: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    __table_args__ = (Index("idx_cgm_user_time", "user_id", "recorded_at"),)

# ─────────────────────────────────────────
# Heart rate log (used for actual GPS extraction per requirement)
# ─────────────────────────────────────────
class UserHrLog(Base):
    __tablename__ = "user_hr_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    heart_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    gps_lat: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    gps_lng: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))

    __table_args__ = (Index("idx_hr_user_time", "user_id", "recorded_at"),)

# ─────────────────────────────────────────
# Exercise log
# ─────────────────────────────────────────
class UserExerciseLog(Base):
    __tablename__ = "user_exercise_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    exercise_type: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    avg_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    calories_burned: Mapped[Optional[float]] = mapped_column(Numeric(7, 1))

    __table_args__ = (Index("idx_ex_user_time", "user_id", "started_at"),)

# ─────────────────────────────────────────
# Weekly activity patterns
# ─────────────────────────────────────────
class UserWeeklyPatterns(Base):
    __tablename__ = "user_weekly_patterns"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (Index("idx_pattern_user", "user_id", "day_of_week"),)

# ─────────────────────────────────────────
# Known locations
# ─────────────────────────────────────────
class UserKnownPlaces(Base):
    __tablename__ = "user_known_places"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    place_name: Mapped[Optional[str]] = mapped_column(String(100))
    place_type: Mapped[Optional[str]] = mapped_column(String(50))
    gps_lat: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    gps_lng: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))

    __table_args__ = (Index("idx_places_user", "user_id"),)

# ─────────────────────────────────────────
# Emotion logs
# ─────────────────────────────────────────
class UserEmotionLog(Base):
    __tablename__ = "user_emotion_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    emotion_label: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="meralion")

    __table_args__ = (Index("idx_daily_emotion_user", "user_id", "recorded_at"),)

class UserEmotionSummary(Base):
    __tablename__ = "user_emotion_summary"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    summary_date: Mapped[date] = mapped_column(Date, nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    primary_emotion: Mapped[Optional[str]] = mapped_column(String(50))

    __table_args__ = (
        UniqueConstraint("user_id", "summary_date", name="uq_user_date"),
        Index("idx_summary_user", "user_id", "summary_date"),
    )

class UserEmergencyContacts(Base):
    __tablename__ = "user_emergency_contacts"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    relationship: Mapped[Optional[str]] = mapped_column(String(50))
    notify_on: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    __table_args__ = (Index("idx_contacts_user", "user_id"),)

class InterventionLog(Base):
    __tablename__ = "intervention_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    trigger_type: Mapped[Optional[str]] = mapped_column(String(50))
    agent_decision: Mapped[Optional[str]] = mapped_column(Text)
    message_sent: Mapped[Optional[str]] = mapped_column(Text)
    user_ack: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

class ErrorLog(Base):
    __tablename__ = "error_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    service: Mapped[Optional[str]] = mapped_column(String(50))
    error_msg: Mapped[Optional[str]] = mapped_column(Text)
    payload: Mapped[Optional[str]] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(DateTime, default=_now)

# ─────────────────────────────────────────
# Logs (Tasks, Rewards, Food, etc.)
# ─────────────────────────────────────────
class UserFoodLog(Base):
    __tablename__ = "user_food_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    food_name: Mapped[str] = mapped_column(String(100), nullable=False)
    meal_type: Mapped[str] = mapped_column(String(10), nullable=False)
    gi_level: Mapped[str] = mapped_column(String(6), nullable=False)
    total_calories: Mapped[float] = mapped_column(Numeric(6, 1), nullable=False)

class DynamicTaskLog(Base):
    __tablename__ = "dynamic_task_log"
    task_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    task_content: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False) # Maps nicely to JSON/TEXT behind scenes
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_now)
    task_status: Mapped[str] = mapped_column(String(18), default="pending", nullable=False)
    target_lat: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    target_lng: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime) # matched schema to our logical expires_at
    reward_points: Mapped[int] = mapped_column(Integer, default=0)

class DynamicTaskRule(Base):
    __tablename__ = "dynamic_task_rule"
    rule_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36))
    base_calorie: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    trigger_threshold: Mapped[float] = mapped_column(Numeric(3, 2), default=0.6, nullable=False)
    
    # Existing default points for old code backwards-compatibility, could be removed but we keep them for reward logic
    meal_pts: Mapped[int] = mapped_column(Integer, default=20)
    quiz_base_pts: Mapped[int] = mapped_column(Integer, default=10)
    quiz_bonus_pts: Mapped[int] = mapped_column(Integer, default=5)
    weekly_pts: Mapped[int] = mapped_column(Integer, default=30)
    exercise_pts: Mapped[int] = mapped_column(Integer, default=50)

    is_active: Mapped[int] = mapped_column(SmallInteger, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

class RoutineTaskLog(Base):
    __tablename__ = "routine_task_log"
    task_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    task_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reward_points: Mapped[int] = mapped_column(Integer, default=0)

class RewardLog(Base):
    __tablename__ = "reward_log"
    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    total_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accumulated_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consumed_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

# ─────────────────────────────────────────
# Aggregation Pipelines
# ─────────────────────────────────────────
class UserGlucoseDailyStats(Base):
    __tablename__ = "user_glucose_daily_stats"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    stat_date: Mapped[date] = mapped_column(Date, nullable=False)
    avg_glucose: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    peak_glucose: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    nadir_glucose: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    glucose_sd: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    tir_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 1))
    tbr_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 1))
    tar_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 1))
    data_points: Mapped[Optional[int]] = mapped_column(Integer)
    is_realtime: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    __table_args__ = (UniqueConstraint("user_id", "stat_date", name="uk_daily_user_date"),)

class UserGlucoseWeeklyProfile(Base):
    __tablename__ = "user_glucose_weekly_profile"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    profile_date: Mapped[date] = mapped_column(Date, nullable=False)
    window_start: Mapped[date] = mapped_column(Date, nullable=False)
    avg_glucose: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    peak_glucose: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    nadir_glucose: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    glucose_sd: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    cv_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 1))
    tir_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 1))
    tbr_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 1))
    tar_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 1))
    avg_delta_vs_prior_7d: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    data_points: Mapped[Optional[int]] = mapped_column(Integer)
    coverage_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 1))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    __table_args__ = (UniqueConstraint("user_id", "profile_date", name="uk_weekly_user_date"),)


# Kept for compatibility with api routes requirement
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
