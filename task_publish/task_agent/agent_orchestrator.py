import logging
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, text
from task_publish.db.models import DynamicTaskLog, RewardLog
from task_publish.utils.math import haversine

logger = logging.getLogger(__name__)

def daily_task_guard(db: Session, user_id: str) -> bool:
    """
    Returns True (= skip) if ANY dynamic task already exists for
    this user today, regardless of status.
    """
    stmt = select(1).where(
        DynamicTaskLog.user_id == user_id,
        func.date(DynamicTaskLog.created_at) == date.today()
    ).limit(1)
    
    exists = db.scalar(stmt)
    return exists is not None

def log_skip(user_id: str, trigger_source: str, reason: str):
    logger.info(f"Skipped trigger for {user_id} via {trigger_source}: {reason}")

def run(db: Session, user_id: str, trigger_source: str):
    if daily_task_guard(db, user_id):
        log_skip(user_id, trigger_source, reason="task_exists_today")
        return
    # proceed to ContextLoader -> RuleEngine -> MapTool -> UserInteraction Node etc.
    # The actual execution flow happens when user selects the destination,
    # then LangGraph subgraph is invoked.
    pass

GEOFENCE_M = 200

class TaskNotActive(Exception):
    pass

def award_points(db: Session, user_id: str, delta: int):
    # Called inside caller transaction. Do NOT open new transaction here.
    db.execute(text("""
        INSERT INTO reward_log (user_id, total_points, accumulated_points)
        VALUES (:ur, :dt, :da)
        ON CONFLICT (user_id) DO UPDATE SET
            total_points       = reward_log.total_points       + EXCLUDED.total_points,
            accumulated_points = reward_log.accumulated_points + EXCLUDED.accumulated_points,
            updated_at         = NOW()
    """), {"ur": user_id, "dt": delta, "da": delta})


def verify_arrival(db: Session, task_id: int, ulat: float, ulng: float) -> dict:
    try:
        t = db.query(DynamicTaskLog).with_for_update().filter(DynamicTaskLog.task_id == task_id).first()
        if not t:
            raise TaskNotActive("Task not found")

        if t.task_status != 'pending':
            db.rollback()
            raise TaskNotActive("Task status is not pending")

        # Fallback if no target given
        if t.target_lat is None or t.target_lng is None:
            db.rollback()
            return {"passed": False, "distance_m": -1, "threshold_m": GEOFENCE_M}

        d = haversine(ulat, ulng, float(t.target_lat), float(t.target_lng))
        
        if d <= GEOFENCE_M:
            t.task_status = 'completed'
            t.completed_at = text("NOW()")
            
            # Award points logic
            award_points(db, t.user_id, t.reward_points)
            
            db.commit()
            return {"passed": True,  "distance_m": round(d)}
        else:
            db.rollback()
            return {"passed": False, "distance_m": round(d), "threshold_m": GEOFENCE_M}

    except Exception as e:
        db.rollback()
        raise e

def get_flower_state(db: Session, user_id: str) -> dict:
    stmt = select(RewardLog.accumulated_points).where(RewardLog.user_id == user_id)
    pts = db.scalar(stmt) or 0
    return {
        "bloomed_count":    pts // 100,
        "current_progress": pts %  100,
        "seed_active":      True
    }
