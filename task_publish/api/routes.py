
import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, File, UploadFile, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from task_publish.db.session import get_db
from task_publish.db.models import DynamicTaskLog, RewardLog, QuizBank, RoutineTaskLog, User, UserExerciseLog, UserCgmLog, DynamicTaskRule, UserHrLog
from task_publish.task_agent import agent_orchestrator
from task_publish.task_agent.graph import copy_subgraph
from task_publish.task_agent.context_loader import fetch_context
from task_publish.task_agent.rule_engine import get_rule_for_user, calculate
from task_publish.api.routine_tasks import submit_meal_photo, fetch_daily_quiZ

router = APIRouter()

# Schema inputs
class SelectDestinationReq(BaseModel):
    park_index: int

class ArriveReq(BaseModel):
    lat: float
    lng: float

class TriggerReq(BaseModel):
    user_id: str

class QuizSubmitReq(BaseModel):
    option: str

class WeeklyWaistReq(BaseModel):
    value_cm: float

class WeeklyWeightReq(BaseModel):
    value_kg: float

class MockSyncReq(BaseModel):
    user_id: str
    calories_burned: float
    cgm_value: float
    lat: Optional[float] = 1.2838  # Default CBD
    lng: Optional[float] = 103.8511

# --- 8.2 Dynamic exercise tasks ---

@router.get("/tasks/dynamic/active")
def get_active_dynamic_task(user_id: str, db: Session = Depends(get_db)):
    """Returns the active dynamic task or null (Section 8.2)"""
    task = db.query(DynamicTaskLog).filter(
        DynamicTaskLog.user_id == user_id,
        DynamicTaskLog.task_status.in_(['awaiting_selection', 'pending'])
    ).first()

    if not task:
        return {"task": None}

    if task.task_status == "awaiting_selection":
        return {
            "task_id": task.task_id,
            "task_status": "awaiting_selection",
            "expires_at": task.expires_at.isoformat() if task.expires_at else None,
            "parks": task.task_content.get("parks", [])
        }
    
    # pending status
    return {
        "task_id": task.task_id,
        "task_status": "pending",
        "expires_at": task.expires_at.isoformat() if task.expires_at else None,
        "title": task.task_content.get("title", ""),
        "body": task.task_content.get("body", ""),
        "cta": task.task_content.get("cta", ""),
        "destination": task.task_content.get("destination", {})
    }

@router.post("/tasks/dynamic/{task_id}/select-destination")
async def select_destination(task_id: int, req: SelectDestinationReq, user_id: str, db: Session = Depends(get_db)):
    task = db.query(DynamicTaskLog).filter(
        DynamicTaskLog.task_id == task_id,
        DynamicTaskLog.user_id == user_id,
        DynamicTaskLog.task_status == 'awaiting_selection'
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found or not in awaiting_selection state")

    parks = task.task_content.get("parks", [])
    if req.park_index < 0 or req.park_index >= len(parks):
        raise HTTPException(status_code=400, detail="Invalid park index")

    selected_park = parks[req.park_index]
    
    # Reload Context & Rules for LangGraph execution state
    ctx = fetch_context(db, user_id)
    rule = get_rule_for_user(db, user_id)
    rule_res = calculate(ctx, rule)
    
    # Execute actual Agent (SeaLion Analyst -> Advisor -> Writer)
    state_in = {
        "user_id": user_id,
        "trigger_source": "user_selection",
        "user_profile": ctx["user_profile"],
        "calories_burned_today": ctx["calories_burned_today"],
        "avg_bg_last_2h": ctx["avg_bg_last_2h"],
        "exercise_history": ctx["exercise_history"],
        "last_gps": ctx["last_gps"],
        "rule": dict(rule) if hasattr(rule, "items") else rule,
        "rule_result": rule_res,
        "selected_park": selected_park,
        "park_candidates": parks,
    }
    
    # Run graph asynchronously
    final_state = await copy_subgraph.ainvoke(state_in)
    
    if "task_content" not in final_state or not final_state["task_content"]:
        raise HTTPException(status_code=500, detail="Failed to generate task content using LangGraph")

    content = final_state["task_content"]
    content["destination"] = selected_park

    task.target_lat = selected_park["lat"]
    task.target_lng = selected_park["lng"]
    task.task_content = content
    task.task_status = 'pending'
    db.commit()

    return {"status": "success"}

@router.post("/tasks/dynamic/{task_id}/arrive")
def arrive_at_destination(task_id: int, req: ArriveReq, db: Session = Depends(get_db)):
    try:
        res = agent_orchestrator.verify_arrival(db, task_id, req.lat, req.lng)
        if not res["passed"]:
            raise HTTPException(status_code=422, detail=res)
        return res
    except agent_orchestrator.TaskNotActive as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/internal/user-context/{user_id}")
def get_user_context(user_id: str, db: Session = Depends(get_db)):
    ctx = fetch_context(db, user_id)
    rule = get_rule_for_user(db, user_id)
    rule_res = calculate(ctx, rule)
    return {
        "context": ctx,
        "rule": dict(rule) if hasattr(rule, "items") else rule,
        "rule_result": rule_res
    }

@router.post("/internal/agent/trigger")
def internal_trigger(req: TriggerReq, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Admin only. Triggers orchestrator
    agent_orchestrator.run(db, req.user_id, "admin")
    return {"status": "triggered"}

@router.post("/internal/mock/sync-data")
def mock_sync_data(req: MockSyncReq, db: Session = Depends(get_db)):
    # Add User and Rule if absent for testing
    user = db.query(User).filter(User.user_id == req.user_id).first()
    if not user:
        db.add(User(
            user_id=req.user_id, 
            name="Demo User",
            weight_kg=80.0,
            height_cm=175.0,
            gender="male"
        ))
        db.add(DynamicTaskRule(user_id=req.user_id, base_calorie=300, trigger_threshold=0.6))
        db.commit()

    # Drop latest exercise
    db.add(UserExerciseLog(
        user_id=req.user_id,
        exercise_type="walking",
        calories_burned=req.calories_burned,
        started_at=datetime.utcnow() - timedelta(minutes=10),
        ended_at=datetime.utcnow()
    ))
    # Drop latest CGM
    db.add(UserCgmLog(
        user_id=req.user_id,
        glucose=req.cgm_value,
        recorded_at=datetime.utcnow()
    ))
    # Drop latest HR for GPS location parsing
    db.add(UserHrLog(
        user_id=req.user_id,
        heart_rate=80,
        gps_lat=req.lat,
        gps_lng=req.lng,
        recorded_at=datetime.utcnow()
    ))
    db.commit()
    return {"status": "synced"}

# --- Test Utils ---

@router.delete("/internal/test/reset-tasks")
def reset_tasks_for_testing(user_id: str, db: Session = Depends(get_db)):
    """DEV ONLY: Delete all dynamic tasks for a user so the daily guard can re-trigger."""
    deleted = db.query(DynamicTaskLog).filter(DynamicTaskLog.user_id == user_id).delete()
    db.commit()
    return {"deleted": deleted, "user_id": user_id}

# --- 8.3 Points and flower ---

@router.get("/points/summary")
def get_points_summary(user_id: str, db: Session = Depends(get_db)):
    summary = db.query(RewardLog).filter(RewardLog.user_id == user_id).first()
    if not summary:
        return {"total_points": 0, "accumulated_points": 0, "consumed_points": 0}
    
    return {
        "total_points": summary.total_points,
        "accumulated_points": summary.accumulated_points,
        "consumed_points": summary.consumed_points
    }

@router.get("/points/flower")
def get_points_flower(user_id: str, db: Session = Depends(get_db)):
    return agent_orchestrator.get_flower_state(db, user_id)

# --- 8.1 Routine tasks (Stubs) ---

@router.get("/tasks/daily")
def get_daily_tasks():
    return {"status": "stubbed"}

@router.post("/tasks/meal-photo")
async def upload_meal_photo(file: UploadFile = File(...), user_id: str = Header(...), db: Session = Depends(get_db)):
    # Read file temporarily
    contents = await file.read()
    # Save to temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
        
    try:
        res = submit_meal_photo(db, user_id, tmp_path)
    finally:
        os.remove(tmp_path)
        
    return res

@router.get("/tasks/quiz/today")
def get_quiz_today(user_id: str, db: Session = Depends(get_db)):
    return fetch_daily_quiZ(db, user_id)

@router.post("/tasks/quiz/submit")
def submit_quiz(req: QuizSubmitReq):
    return {"status": "stubbed"}

@router.post("/tasks/weekly/waist")
def submit_waist(req: WeeklyWaistReq):
    return {"status": "stubbed"}

@router.post("/tasks/weekly/weight")
def submit_weight(req: WeeklyWeightReq):
    return {"status": "stubbed"}

@router.get("/tasks/weekly")
def get_weekly_tasks():
    return {"status": "stubbed"}
