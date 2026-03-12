"""
utils/mock_data.py
模拟用户健康数据，用于开发和测试
"""
from datetime import datetime, timedelta
from schemas.health import (
    HealthSnapshot, GlucosePattern, GlucoseReading,
    RenalIndicators, MealRecord, MedicationStatus,
    ExerciseRecord, BehaviorPattern,
)
from utils.time_utils import now_sgt, SGT


def get_mock_user_profile(user_id: str = "user_001") -> dict:
    """模拟用户档案"""
    profiles = {
        "user_001": {
            "user_id": "user_001",
            "name": "陈先生",
            "age": 55,
            "language": "Chinese",
            "conditions": ["Type 2 Diabetes", "高血压"],
            "medications": [
                {"name": "Metformin 500mg", "dosage": "500mg", "times": ["08:00", "20:00"]},
                {"name": "Amlodipine 5mg", "dosage": "5mg", "times": ["08:00"]},
            ],
            "preferences": {
                "reminder_time": "08:00",
                "diet": "低碳水",
                "exercise_time": "17:00",
                "calories_goal": 300,
            },
            "emergency_contacts": [{"name": "陈太太", "phone": "+65 9123 4567"}],
            "doctor": {"name": "Dr. Lim", "clinic": "SGH Diabetes Centre"},
        },
        "user_002": {
            "user_id": "user_002",
            "name": "Mr Tan",
            "age": 42,
            "language": "English",
            "conditions": ["Type 2 Diabetes"],
            "medications": [
                {"name": "Metformin 1000mg", "dosage": "1000mg", "times": ["09:00"]},
            ],
            "preferences": {
                "reminder_time": "09:00",
                "diet": "halal",
                "exercise_time": "07:00",
                "calories_goal": 400,
            },
            "emergency_contacts": [],
            "doctor": {"name": "Dr. Wong", "clinic": "NUH Endocrine"},
        },
    }
    return profiles.get(user_id, profiles["user_001"])


def get_mock_health_snapshot(
    user_id: str = "user_001",
    scenario: str = "normal",
) -> HealthSnapshot:
    """
    模拟健康快照
    scenario: normal / pre_exercise_risk / high_glucose / renal_concern / medication_missed
    """
    now = now_sgt()
    base_readings = [
        GlucoseReading(value=5.8, timestamp=now - timedelta(hours=6), context="fasting"),
        GlucoseReading(value=8.2, timestamp=now - timedelta(hours=4), context="post_meal"),
        GlucoseReading(value=6.5, timestamp=now - timedelta(hours=2), context="random"),
        GlucoseReading(value=6.0, timestamp=now - timedelta(hours=1), context="random"),
    ]

    snapshot = HealthSnapshot(
        user_id=user_id,
        timestamp=now,
        glucose=GlucosePattern(
            recent_readings=base_readings,
            avg_fasting=5.8,
            avg_post_meal=8.2,
            has_dawn_phenomenon=False,
            time_in_range_pct=75.0,
            trend="stable",
        ),
        latest_hba1c=7.2,
        last_hba1c_date=now - timedelta(days=80),
        renal=RenalIndicators(egfr=85.0, egfr_previous=88.0, egfr_trend="stable"),
        today_meals=[
            MealRecord(meal_type="breakfast", description="Kaya toast + kopi-o",
                       photo_uploaded=True, estimated_calories=350, gi_level="medium",
                       timestamp=now.replace(hour=8, minute=0)),
        ],
        today_medications=[
            MedicationStatus(medication_name="Metformin 500mg", dosage="500mg",
                             scheduled_time="08:00", taken=True,
                             taken_at=now.replace(hour=8, minute=5)),
        ],
        today_exercise=[
            ExerciseRecord(
                exercise_type="walking",
                start_time=now - timedelta(minutes=45),
                end_time=now - timedelta(minutes=15),
                duration_min=30,
                calories_burned=120.0,
                avg_heart_rate=110,
                timestamp=now - timedelta(minutes=15)
            )
        ],
        today_calories=120.0,
        heart_rate=72,
        blood_pressure_sys=135,
        blood_pressure_dia=85,
        usual_exercise_time="17:00",
        medication_adherence_pct=90.0,
        recent_chat_insights=[
            "用户今早反映感觉精神不错",
            "用户询问了关于运动前是否需要加餐的问题",
        ],
        reported_symptoms=[],
        emotional_state="neutral",
        last_checkup_date=now - timedelta(days=75),
    )

    if scenario == "pre_exercise_risk":
        snapshot.glucose.recent_readings[-1] = GlucoseReading(
            value=4.2, timestamp=now - timedelta(minutes=30), context="random"
        )
        snapshot.glucose.avg_fasting = 4.3
        snapshot.today_meals = [
            MealRecord(meal_type="breakfast", description="小份麦片",
                       timestamp=now - timedelta(hours=4)),
        ]
        snapshot.recent_chat_insights.append("用户说打算下午去跑步")

    elif scenario == "high_glucose":
        snapshot.glucose.recent_readings = [
            GlucoseReading(value=9.5, timestamp=now - timedelta(hours=6), context="fasting"),
            GlucoseReading(value=14.2, timestamp=now - timedelta(hours=3), context="post_meal"),
            GlucoseReading(value=11.8, timestamp=now - timedelta(hours=1), context="random"),
        ]
        snapshot.glucose.avg_fasting = 9.5
        snapshot.glucose.avg_post_meal = 14.2
        snapshot.glucose.trend = "worsening"
        snapshot.today_meals.append(
            MealRecord(meal_type="lunch", description="Nasi Lemak + Milo dinosaur",
                       estimated_calories=850, gi_level="high",
                       timestamp=now - timedelta(hours=3))
        )

    elif scenario == "renal_concern":
        snapshot.renal = RenalIndicators(
            egfr=52.0, egfr_previous=58.0, egfr_trend="declining",
            proteinuria=350.0, has_foam_urine=True,
            last_renal_test_date=now - timedelta(days=60),
        )
        snapshot.reported_symptoms = ["口干", "容易疲劳", "泡沫尿"]
        snapshot.recent_chat_insights.append("用户反馈最近尿液有很多泡沫，感到口干")

    elif scenario == "medication_missed":
        snapshot.today_medications = [
            MedicationStatus(medication_name="Metformin 500mg", dosage="500mg",
                             scheduled_time="08:00", taken=False),
        ]
        snapshot.medication_adherence_pct = 60.0
        snapshot.glucose.recent_readings[-1] = GlucoseReading(
            value=12.5, timestamp=now - timedelta(hours=1), context="random"
        )

    return snapshot


def get_mock_behavior_pattern(user_id: str = "user_001") -> BehaviorPattern:
    """模拟行为模式"""
    return BehaviorPattern(
        user_id=user_id,
        week_start=now_sgt() - timedelta(days=now_sgt().weekday()),
        avg_daily_calories=250.0,
        exercise_days_per_week=3,
        exercise_preferred_time="17:00",
        meal_regularity_score=0.7,
        medication_adherence_pct=85.0,
        task_completion_rate=0.65,
        glucose_control_score=0.6,
        consecutive_completion_days=3,
    )


def get_mock_chat_insights(scenario: str = "normal") -> list[str]:
    """模拟聊天记录提取的关键信息"""
    insights = {
        "normal": [
            "用户今早心情不错，和家人一起吃了早餐",
            "用户询问了新加坡的低GI食物推荐",
            "用户表示最近运动后感觉精力更好",
        ],
        "emotional": [
            "用户最近情绪低落，提到控糖压力大",
            "用户说每次测血糖都很焦虑",
            "用户表示不想继续吃药了",
        ],
        "symptoms": [
            "用户反馈口干、容易疲劳",
            "用户提到最近视力有些模糊",
            "用户说晚上起夜次数增多",
        ],
    }
    return insights.get(scenario, insights["normal"])
