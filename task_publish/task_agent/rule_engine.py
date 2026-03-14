from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

def get_rule_for_user(db: Session, user_id: str) -> Dict[str, Any]:
    # fetch per-user
    r = db.execute(text("SELECT * FROM dynamic_task_rule WHERE user_id = :u AND is_active=1"), {"u": user_id}).mappings().first()
    if r:
        return dict(r)
    
    # fetch global default
    g = db.execute(text("SELECT * FROM dynamic_task_rule WHERE user_id IS NULL AND is_active=1")).mappings().first()
    if g:
        return dict(g)
    
    # hard fallback
    return {
        "base_calorie": 300,
        "trigger_threshold": 0.600,
        "exercise_pts": 50,
        "meal_pts": 20,
        "quiz_base_pts": 10,
        "quiz_bonus_pts": 5,
        "weekly_pts": 30
    }

def calculate(ctx: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
    profile = ctx["user_profile"]
    bmi = profile["bmi"]
    
    if   bmi < 18.5: modifier = 0.80
    elif bmi < 25.0: modifier = 1.00
    elif bmi < 30.0: modifier = 1.10
    else:            modifier = 1.20
    
    target = rule["base_calorie"] * modifier
    
    # HARD SAFETY GUARD: BG < 5.0
    if ctx["avg_bg_last_2h"] is not None and ctx["avg_bg_last_2h"] < 5.0:
        target *= 0.70
        
    actual = ctx["calories_burned_today"] or 0.0
    ratio  = actual / target if target > 0 else 1.0
    
    should_trigger = ratio < rule["trigger_threshold"]
    deficit_kcal = max(0, int(target - actual))
    
    return {
        "should_trigger": should_trigger,
        "deficit_kcal": deficit_kcal,
        "adjusted_target": int(target)
    }
