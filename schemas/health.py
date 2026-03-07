"""
schemas/health.py
健康数据 Pydantic v2 模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class GlucoseReading(BaseModel):
    """单条血糖读数"""
    value: float = Field(description="mmol/L")
    timestamp: datetime
    reading_type: str = "cgm"  # cgm / finger_prick / lab
    context: str = "unknown"   # fasting / pre_meal / post_meal / random / dawn


class GlucosePattern(BaseModel):
    """血糖模式分析"""
    recent_readings: list[GlucoseReading] = Field(default_factory=list)
    avg_fasting: Optional[float] = None
    avg_post_meal: Optional[float] = None
    has_dawn_phenomenon: bool = False   # 黎明现象
    time_in_range_pct: Optional[float] = None  # TIR: 在范围内的时间百分比
    trend: str = "stable"  # improving / stable / worsening


class RenalIndicators(BaseModel):
    """肾功能指标"""
    egfr: Optional[float] = Field(default=None, description="mL/min/1.73m²")
    egfr_previous: Optional[float] = None
    egfr_trend: str = "stable"  # improving / stable / declining
    proteinuria: Optional[float] = None  # mg/day
    has_foam_urine: bool = False  # 泡沫尿
    last_renal_test_date: Optional[datetime] = None


class MealRecord(BaseModel):
    """餐食记录"""
    meal_type: str = "unknown"  # breakfast / lunch / dinner / snack
    description: str = ""
    photo_uploaded: bool = False
    estimated_calories: Optional[float] = None
    estimated_carbs_g: Optional[float] = None
    gi_level: str = "unknown"  # low / medium / high
    timestamp: Optional[datetime] = None


class MedicationStatus(BaseModel):
    """用药状态"""
    medication_name: str
    dosage: str = ""
    scheduled_time: str = ""  # HH:MM
    taken: bool = False
    taken_at: Optional[datetime] = None


class ExerciseRecord(BaseModel):
    """运动记录"""
    exercise_type: str = ""  # walking / jogging / swimming / cycling / tai_chi
    duration_min: int = 0
    steps: int = 0
    heart_rate_avg: Optional[int] = None
    timestamp: Optional[datetime] = None


class HealthSnapshot(BaseModel):
    """用户当前健康快照 —— 传入智能引擎的核心数据"""
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.now)

    # 血糖
    glucose: GlucosePattern = Field(default_factory=GlucosePattern)
    latest_hba1c: Optional[float] = None
    last_hba1c_date: Optional[datetime] = None

    # 肾功能
    renal: RenalIndicators = Field(default_factory=RenalIndicators)

    # 今日记录
    today_meals: list[MealRecord] = Field(default_factory=list)
    today_medications: list[MedicationStatus] = Field(default_factory=list)
    today_exercise: list[ExerciseRecord] = Field(default_factory=list)
    today_steps: int = 0

    # 生命体征
    heart_rate: Optional[int] = None
    blood_pressure_sys: Optional[int] = None
    blood_pressure_dia: Optional[int] = None

    # 行为模式
    usual_exercise_time: Optional[str] = None  # 常规运动时间 HH:MM
    usual_meal_times: dict = Field(default_factory=dict)
    medication_adherence_pct: float = 100.0  # 近30天服药率

    # 聊天记录摘要（来自 chatbot 的 insights）
    recent_chat_insights: list[str] = Field(default_factory=list)
    reported_symptoms: list[str] = Field(default_factory=list)  # 用户自报症状
    emotional_state: str = "neutral"

    # 复诊
    last_checkup_date: Optional[datetime] = None
    next_scheduled_checkup: Optional[datetime] = None


class BehaviorPattern(BaseModel):
    """行为模式（周维度统计）"""
    user_id: str
    week_start: Optional[datetime] = None
    avg_daily_steps: int = 0
    exercise_days_per_week: int = 0
    exercise_preferred_time: str = "afternoon"
    meal_regularity_score: float = 0.0  # 0-1，用餐规律性
    medication_adherence_pct: float = 100.0
    task_completion_rate: float = 0.0  # 上周任务完成率
    glucose_control_score: float = 0.0  # 0-1
    consecutive_completion_days: int = 0  # 连续完成天数
