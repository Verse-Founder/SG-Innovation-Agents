import os
import sys
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from task_publish.config import settings
from task_publish.db.models import (
    Base, User, UserCgmLog, UserHrLog, UserExerciseLog, 
    DynamicTaskRule, UserKnownPlaces, RewardLog, QuizBank
)

def seed_db():
    # Force PostgreSQL connection directly for seeding script to bypass any python-dotenv loading issues.
    direct_url = "postgresql+psycopg2://weichayi@localhost/task_publish"
    engine = create_engine(direct_url)
    Base.metadata.create_all(bind=engine)
    
    with Session(engine) as db:
        print("Clearing old data (if any)...")
        # Just simple cleanup for the seed tables we care about
        db.query(UserExerciseLog).delete()
        db.query(UserCgmLog).delete()
        db.query(UserHrLog).delete()
        db.query(DynamicTaskRule).delete()
        db.query(UserKnownPlaces).delete()
        db.query(RewardLog).delete()
        db.query(QuizBank).delete()
        db.query(User).delete()
        db.commit()

        print("Seeding Case 1: Active User (Should NOT trigger dynamic tasks)")
        # BMI = 22.8 (normal) -> Target Cal = 300 * 1.0 = 300
        # Actually burned 400 kcal -> Ratio 400/300 = 1.33 >= 0.6 -> Does not trigger.
        active_user_id = "demo_user_active"
        db.add(User(
            user_id=active_user_id, name="Alice (Active)", gender="female",
            birth_year=1990, height_cm=165.0, weight_kg=62.0, waist_cm=72.0
        ))
        db.add(DynamicTaskRule(user_id=active_user_id, base_calorie=300, trigger_threshold=0.6))
        db.add(RewardLog(user_id=active_user_id, total_points=50))
        
        # High calories burned today
        db.add(UserExerciseLog(
            user_id=active_user_id, exercise_type="cardio",
            started_at=datetime.utcnow() - timedelta(hours=3),
            ended_at=datetime.utcnow() - timedelta(hours=2, minutes=15),
            calories_burned=400.0, avg_heart_rate=145
        ))
        # Normal BG
        db.add(UserCgmLog(
            user_id=active_user_id, recorded_at=datetime.utcnow() - timedelta(minutes=10), glucose=6.5
        ))
        db.add(UserHrLog(
            user_id=active_user_id, recorded_at=datetime.utcnow() - timedelta(minutes=5),
            heart_rate=75, gps_lat=1.3521, gps_lng=103.8198
        ))

        print("Seeding Case 2: Sedentary User (SHOULD trigger dynamic tasks)")
        # BMI = 31.1 (obese) -> Target Cal = 300 * 1.2 = 360
        # Actually burned 50 kcal -> Ratio 50/360 = 0.13 < 0.6 -> WILL TRIGGER WALK.
        sedentary_user_id = "demo_user_sedentary"
        db.add(User(
            user_id=sedentary_user_id, name="Bob (Sedentary)", gender="male",
            birth_year=1985, height_cm=175.0, weight_kg=95.0, waist_cm=102.0
        ))
        db.add(DynamicTaskRule(user_id=sedentary_user_id, base_calorie=300, trigger_threshold=0.6))
        db.add(RewardLog(user_id=sedentary_user_id, total_points=10))
        
        # Low calories burned today
        db.add(UserExerciseLog(
            user_id=sedentary_user_id, exercise_type="walking",
            started_at=datetime.utcnow() - timedelta(hours=5),
            ended_at=datetime.utcnow() - timedelta(hours=4, minutes=50),
            calories_burned=50.0, avg_heart_rate=100
        ))
        # Normal BG (if < 5.0 it would reduce target safely, let's keep it normal)
        db.add(UserCgmLog(
            user_id=sedentary_user_id, recorded_at=datetime.utcnow() - timedelta(minutes=10), glucose=7.2
        ))
        # GPS in CBD
        db.add(UserHrLog(
            user_id=sedentary_user_id, recorded_at=datetime.utcnow() - timedelta(minutes=5),
            heart_rate=80, gps_lat=1.2838, gps_lng=103.8511
        ))

        print("Seeding Case 3: Hypoglycemia Risk User (Safety Guard Triggered)")
        # BMI = 20.7 (normal) -> Base Target 300 
        # BG < 5.0 -> Adjusted Target = 300 * 0.7 = 210
        # Actuall burned 200 -> 200/210 = 0.95 >= 0.6 ! (Will NOT trigger dynamic task, safe!)
        hypo_user_id = "demo_user_hypo"
        db.add(User(
            user_id=hypo_user_id, name="Charlie (Low BG)", gender="male",
            birth_year=1970, height_cm=170.0, weight_kg=60.0, waist_cm=78.0
        ))
        db.add(DynamicTaskRule(user_id=hypo_user_id, base_calorie=300, trigger_threshold=0.6))
        db.add(RewardLog(user_id=hypo_user_id, total_points=0))
        
        db.add(UserExerciseLog(
            user_id=hypo_user_id, exercise_type="walking",
            started_at=datetime.utcnow() - timedelta(hours=6),
            ended_at=datetime.utcnow() - timedelta(hours=5, minutes=30),
            calories_burned=200.0, avg_heart_rate=110
        ))
        # DANGEROUS LOW BG
        db.add(UserCgmLog(
            user_id=hypo_user_id, recorded_at=datetime.utcnow() - timedelta(minutes=10), glucose=4.2
        ))
        db.add(UserHrLog(
            user_id=hypo_user_id, recorded_at=datetime.utcnow() - timedelta(minutes=5),
            heart_rate=65, gps_lat=1.3138, gps_lng=103.8911
        ))

        print("Seeding Quiz Bank (For Routine Tasks)")
        db.add(QuizBank(
            question="What is the recommended HbA1c target for most adults with diabetes?",
            option_a="Less than 6.0%",
            option_b="Less than 7.0%",
            option_c="Less than 8.0%",
            option_d="Less than 9.0%",
            correct_option="b",
            explanation="The ADA generally recommends an HbA1c target of < 7.0% for many nonpregnant adults."
        ))

        db.commit()
        print("Database seeded successfully with 3 distinct test profiles!")

if __name__ == "__main__":
    seed_db()
