from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date

def fetch_context(db: Session, user_id: str) -> Dict[str, Any]:
    # user profile
    profile_row = db.execute(text("SELECT name, language_pref FROM users WHERE user_id = :u"), {"u": user_id}).fetchone()
    # BMI/Height/Weight is normally in another table, for this module we mock or query assuming custom integration
    profile = {
        "name": profile_row.name if profile_row else "User",
        "language_pref": profile_row.language_pref if profile_row else "en",
        "weight_kg": 70.0,
        "height_cm": 170.0,
        "bmi": 70.0 / ((170.0/100)**2)
    }

    # calories_burned_today
    cbt = db.scalar(text("""
        SELECT COALESCE(SUM(calories_burned), 0)
        FROM user_exercise_log
        WHERE user_id = :u AND date(started_at) = date('now')
    """), {"u": user_id})

    # bg avg last 2h
    bg = db.scalar(text("""
        SELECT AVG(glucose)
        FROM user_cgm_log
        WHERE user_id = :u AND datetime(recorded_at) >= datetime('now', '-2 hours')
    """), {"u": user_id})

    # history last 3 walking (mock default 'walking')
    history_rows = db.execute(text("""
        SELECT exercise_type as type, duration_min, calories_burned
        FROM user_exercise_log
        WHERE user_id = :u AND exercise_type = 'walking'
        ORDER BY started_at DESC
        LIMIT 3
    """), {"u": user_id}).fetchall()
    history = [{"type": h.type, "duration_min": h.duration_min, "calories_burned": h.calories_burned} for h in history_rows]

    # location mock (last_gps in real system)
    last_gps = {"lat": 1.3521, "lng": 103.8198}

    return {
        "user_profile": profile,
        "calories_burned_today": cbt or 0.0,
        "avg_bg_last_2h": bg,
        "exercise_history": history,
        "last_gps": last_gps
    }
