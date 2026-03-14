from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, exc, text

from task_publish.db.models import RoutineTaskLog, QuizBank, RewardLog, User
from task_publish.task_agent.agent_orchestrator import award_points

try:
    from src.vision_agent.agent import VisionAgent
    from src.vision_agent.llm.gemini import GeminiVLM
    VISION_ENABLED = True
except ImportError:
    VISION_ENABLED = False


def log_routine_task(db: Session, user_id: str, task_type: str, period: str, expires_at, points: int) -> RoutineTaskLog:
    """Inserts a pending routine task."""
    task = RoutineTaskLog(
        user_id=user_id,
        task_type=task_type,
        period=period,
        expires_at=expires_at,
        reward_points=points,
        task_status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def fetch_daily_quiZ(db: Session) -> Optional[QuizBank]:
    """Fetches quiz logic day_of_year % total_active."""
    total = db.scalar(select(func.count(QuizBank.id)).where(QuizBank.is_active == 1))
    if not total or total == 0:
        return None
        
    day = date.today().timetuple().tm_yday
    idx = day % total
    
    # Use sort_order then id for stable queries
    q = db.scalars(select(QuizBank).where(QuizBank.is_active == 1).order_by(QuizBank.sort_order, QuizBank.id).offset(idx).limit(1)).first()
    return q

def submit_meal_photo(db: Session, user_id: str, file_path_or_bytes: Any) -> Dict[str, Any]:
    """Uses real VisionAgent to verify food and reward meal pts."""
    if not VISION_ENABLED:
        return {"passed": False, "reason": "vision plugin missing"}
        
    vlm = GeminiVLM()
    agent = VisionAgent(vlm=vlm)
    res = agent.analyze(file_path_or_bytes)
    
    if res.scene_type == "FOOD":
        # Get rule for pts
        from task_publish.task_agent.rule_engine import get_rule_for_user
        rule = get_rule_for_user(db, user_id)
        
        # log in routine tasks mock for period = today_meal
        import datetime
        period = f"meal_{datetime.date.today().isoformat()}"
        
        try:
            db.execute(text("""
                INSERT INTO routine_task_log (user_id, task_type, period, task_status, expires_at, reward_points, completed_at)
                VALUES (:u, 'meal_photo', :p, 'completed', :ea, :pts, :now)
            """), {
                "u": user_id, "p": period, "ea": datetime.datetime.utcnow() + datetime.timedelta(days=1),
                "pts": rule["meal_pts"], "now": datetime.datetime.utcnow()
            })
            award_points(db, user_id, rule["meal_pts"])
            db.commit()
            return {"passed": True, "points": rule["meal_pts"], "confidence": res.confidence}
        except exc.IntegrityError:
            db.rollback()
            return {"passed": False, "reason": "meal already logged today"}
            
    return {"passed": False, "reason": "not recognized as food", "type": res.scene_type}
