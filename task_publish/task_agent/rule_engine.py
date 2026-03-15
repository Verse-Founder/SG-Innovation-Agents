from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

def get_rule_for_user(db: Session, user_id: str) -> Dict[str, Any]:
    r = db.execute(text("SELECT * FROM dynamic_task_rule WHERE user_id = :u AND is_active=1"), {"u": user_id}).mappings().first()
    if r:
        return dict(r)
    return {
        "base_calorie": 300,
        "trigger_threshold": 0.60,
    }

def calculate(ctx: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
    profile = ctx["user_profile"]
    bmi = profile["bmi"]
    
    # ADA Target Calorie Formula
    if bmi < 18.5: 
        modifier = 0.80
    elif bmi < 25.0: 
        modifier = 1.00
    elif bmi < 30.0: 
        modifier = 1.10
    else:            
        modifier = 1.20
    
    target = float(rule.get("base_calorie", 300)) * modifier
    
    # BG Modifier (hypoglycaemia risk)
    avg_bg = ctx.get("avg_bg_last_2h")
    if avg_bg is not None and avg_bg < 5.0:
        target *= 0.70
        
    actual = ctx["calories_burned_today"] or 0.0
    ratio  = actual / target if target > 0 else 1.0
    
    # Threshold check
    should_trigger = ratio < float(rule.get("trigger_threshold", 0.60))
    deficit_kcal = max(0, int(target - actual))
    
    return {
        "should_trigger": should_trigger,
        "deficit_kcal": deficit_kcal,
        "adjusted_target": int(target)
    }
