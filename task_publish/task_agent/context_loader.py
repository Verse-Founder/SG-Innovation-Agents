import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, datetime, timedelta
from task_publish.db.models import User

def fetch_context(db: Session, user_id: str) -> Dict[str, Any]:
    # 1. Fetch user profile and BMI correctly using the ORM
    user = db.query(User).filter(User.user_id == user_id).first()
    bmi = 22.0 # default fallback
    if user:
        bmi = user.bmi
    
    profile = {
        "name": user.name if user else "User",
        "gender": user.gender if user else "other",
        "weight_kg": float(user.weight_kg) if user and user.weight_kg else 70.0,
        "height_cm": float(user.height_cm) if user and user.height_cm else 170.0,
        "bmi": bmi,
        "waist_cm": float(user.waist_cm) if user and user.waist_cm else None,
        "birth_year": user.birth_year if user else None,
    }

    today_start = datetime.combine(date.today(), datetime.min.time())
    two_hours_ago = datetime.utcnow() - timedelta(hours=2)

    # 2. Calories burned today (PostgreSQL-compatible)
    cbt = db.scalar(text("""
        SELECT COALESCE(SUM(calories_burned), 0)
        FROM user_exercise_log
        WHERE user_id = :u AND started_at >= :today
    """), {"u": user_id, "today": today_start})

    # 3. BG avg last 2h (PostgreSQL-compatible)
    bg = db.scalar(text("""
        SELECT AVG(glucose)
        FROM user_cgm_log
        WHERE user_id = :u AND recorded_at >= :cutoff
    """), {"u": user_id, "cutoff": two_hours_ago})

    # 4. History last 3 walking sessions with duration
    history_rows = db.execute(text("""
        SELECT exercise_type,
               calories_burned,
               EXTRACT(EPOCH FROM (ended_at - started_at)) / 60 AS duration_min
        FROM user_exercise_log
        WHERE user_id = :u AND exercise_type = 'walking'
        ORDER BY started_at DESC
        LIMIT 3
    """), {"u": user_id}).fetchall()
    
    history = [{
        "type": h.exercise_type,
        "duration_min": round(h.duration_min) if h.duration_min else 10,
        "calories_burned": float(h.calories_burned or 0)
    } for h in history_rows]

    # 5. GPS from latest HR log (Apple Watch 10-min interval simulation)
    gps_row = db.execute(text("""
        SELECT gps_lat, gps_lng 
        FROM user_hr_log 
        WHERE user_id = :u AND gps_lat IS NOT NULL
        ORDER BY recorded_at DESC LIMIT 1
    """), {"u": user_id}).fetchone()
    
    last_gps = {"lat": float(gps_row.gps_lat), "lng": float(gps_row.gps_lng)} if gps_row else {"lat": 1.3521, "lng": 103.8198}

    return {
        "user_profile": profile,
        "calories_burned_today": float(cbt or 0.0),
        "avg_bg_last_2h": float(bg) if bg else None,
        "exercise_history": history,
        "last_gps": last_gps
    }
