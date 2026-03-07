"""
api/routes.py
FastAPI 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from graph.builder import run_task_agent

router = APIRouter()


class TriggerRequest(BaseModel):
    """触发请求"""
    user_id: str
    trigger_source: str = "chatbot"
    payload: dict = {}


class TaskCompleteRequest(BaseModel):
    """任务完成请求"""
    user_id: str
    task_id: str


@router.post("/trigger/chatbot")
async def trigger_from_chatbot(req: TriggerRequest):
    """接收来自 chatbot 的 task_trigger"""
    try:
        result = run_task_agent(
            user_id=req.user_id,
            trigger_source="chatbot",
            trigger_payload=req.payload,
        )
        return {"status": "ok", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/alert")
async def trigger_from_alert(req: TriggerRequest):
    """接收来自预警 Agent 的信号"""
    try:
        result = run_task_agent(
            user_id=req.user_id,
            trigger_source="alert_agent",
            trigger_payload=req.payload,
        )
        return {"status": "ok", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/doctor")
async def trigger_from_doctor(req: TriggerRequest):
    """接收医生端任务（预留）"""
    try:
        result = run_task_agent(
            user_id=req.user_id,
            trigger_source="doctor",
            trigger_payload=req.payload,
        )
        return {"status": "ok", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{user_id}")
async def get_user_tasks(user_id: str):
    """查询用户当前任务列表"""
    # 在生产环境中应从数据库查询
    result = run_task_agent(user_id=user_id, trigger_source="system")
    return {"status": "ok", "data": result}


@router.post("/tasks/complete")
async def complete_task(req: TaskCompleteRequest):
    """标记任务完成，计算积分"""
    from engine.points_engine import process_task_completion
    from schemas.points import PointsBalance

    # 在生产中应从 DB 获取任务和余额
    current_balance = PointsBalance(user_id=req.user_id)
    transaction, updated_balance = process_task_completion(
        user_id=req.user_id,
        task_id=req.task_id,
        task_category="monitoring",
        task_type="daily_routine",
        current_balance=current_balance,
    )
    return {
        "status": "ok",
        "points_earned": transaction.amount,
        "new_balance": updated_balance.current_balance,
        "streak_days": updated_balance.streak_days,
    }


@router.get("/points/{user_id}")
async def get_points(user_id: str):
    """查询用户积分余额"""
    from schemas.points import PointsBalance
    # 生产环境从 DB 读取
    balance = PointsBalance(user_id=user_id)
    return {"status": "ok", "data": balance.model_dump()}
