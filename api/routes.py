"""
api/routes.py
FastAPI 路由 — 接入数据库层
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from graph.builder import run_task_agent
from db.session import get_session
from db import crud

router = APIRouter()


class TriggerRequest(BaseModel):
    user_id: str
    trigger_source: str = "chatbot"
    payload: dict = {}


class TaskCompleteRequest(BaseModel):
    user_id: str
    task_id: str


class BatchCreateRequest(BaseModel):
    user_id: str
    tasks: list[dict]


# ── 触发路由 ─────────────────────────────────────────────

@router.post("/trigger/chatbot")
async def trigger_from_chatbot(req: TriggerRequest):
    try:
        result = run_task_agent(
            user_id=req.user_id, trigger_source="chatbot",
            trigger_payload=req.payload,
        )
        return {"status": "ok", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/alert")
async def trigger_from_alert(req: TriggerRequest):
    try:
        result = run_task_agent(
            user_id=req.user_id, trigger_source="alert_agent",
            trigger_payload=req.payload,
        )
        return {"status": "ok", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/doctor")
async def trigger_from_doctor(req: TriggerRequest):
    try:
        result = run_task_agent(
            user_id=req.user_id, trigger_source="doctor",
            trigger_payload=req.payload,
        )
        return {"status": "ok", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 数据库路由 ────────────────────────────────────────────

@router.get("/tasks/{user_id}")
async def get_user_tasks(user_id: str, status: Optional[str] = None):
    async with get_session() as session:
        tasks = await crud.get_user_tasks(session, user_id, status=status)
        if not tasks:
            result = run_task_agent(user_id=user_id, trigger_source="system")
            return {"status": "ok", "source": "agent", "data": result}
        return {
            "status": "ok",
            "source": "db",
            "data": [
                {
                    "task_id": t.id, "user_id": t.user_id,
                    "task_type": t.task_type, "category": t.category,
                    "title": t.title, "description": t.description,
                    "caring_message": t.caring_message,
                    "points": t.points, "priority": t.priority,
                    "status": t.status,
                    "deadline": t.deadline.isoformat() if t.deadline else None,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in tasks
            ],
        }


@router.post("/tasks/complete")
async def complete_task(req: TaskCompleteRequest):
    async with get_session() as session:
        completion = await crud.complete_task(session, req.task_id, req.user_id)
        if not completion:
            raise HTTPException(status_code=404, detail="任务不存在或不属于该用户")
        balance = await crud.get_points_balance(session, req.user_id)
        return {
            "status": "ok",
            "points_earned": completion.points_earned,
            "new_balance": balance["current_balance"],
            "total_earned": balance["total_earned"],
        }


@router.post("/tasks/batch")
async def batch_create_tasks(req: BatchCreateRequest):
    created = []
    async with get_session() as session:
        for task_data in req.tasks:
            task = await crud.create_task(session, user_id=req.user_id, **task_data)
            created.append({"task_id": task.id, "title": task.title})
    return {"status": "ok", "created": len(created), "tasks": created}


@router.get("/points/{user_id}")
async def get_points(user_id: str):
    async with get_session() as session:
        balance = await crud.get_points_balance(session, user_id)
        return {"status": "ok", "data": balance}
