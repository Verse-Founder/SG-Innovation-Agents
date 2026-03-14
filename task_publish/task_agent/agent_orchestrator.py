import logging
import json
from datetime import date, datetime
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

from task_publish.task_agent.context_loader import fetch_context
from task_publish.task_agent.rule_engine import get_rule_for_user, calculate
from task_publish.task_agent.map_tool import find_nearby_parks
from task_publish.task_agent.nodes.task_publisher import end_of_today

def run(db: Session, user_id: str, trigger_source: str):
    if daily_task_guard(db, user_id):
        log_skip(user_id, trigger_source, reason="task_exists_today")
        return
    
    # ContextLoader
    ctx = fetch_context(db, user_id)
    
    # RuleEngine
    rule = get_rule_for_user(db, user_id)
    rule_res = calculate(ctx, rule)
    
    if not rule_res["should_trigger"]:
        log_skip(user_id, trigger_source, reason="threshold_not_met")
        return

    # MapTool
    last_gps = ctx["last_gps"]
    parks = find_nearby_parks(db, last_gps["lat"], last_gps["lng"], user_id)
    for i, p in enumerate(parks):
        p["index"] = i  # Inject index

    # Assemble initial state for task publishing
    content = {"parks": parks}

    # Insert Task (Awaiting Selection)
    db.execute(text("""
        INSERT INTO dynamic_task_log (user_id, task_content, task_status, created_at, expires_at, reward_points)
        VALUES (:ur, :tc, :ts, :now, :ea, :rp)
    """), {
        "ur": user_id, 
        "tc": json.dumps(content), 
        "ts": "awaiting_selection", 
        "now": datetime.utcnow(),
        "ea": end_of_today(),
        "rp": rule["exercise_pts"]
    })
    db.commit()
    logger.info(f"Triggered dynamic task awaiting selection for user {user_id}")

GEOFENCE_M = 200

class TaskNotActive(Exception):
    pass

def award_points(db: Session, user_id: str, delta: int):
    # Called inside caller transaction. Do NOT open new transaction here.
    stmt = text("""
        INSERT INTO reward_log (user_id, total_points, accumulated_points, consumed_points, updated_at)
        VALUES (:u, :p, :p, 0, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            total_points = reward_log.total_points + excluded.total_points,
            accumulated_points = reward_log.accumulated_points + excluded.accumulated_points,
            updated_at = CURRENT_TIMESTAMP
    """)
    db.execute(stmt, {"u": user_id, "p": delta})


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
            t.completed_at = datetime.utcnow()
            
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
