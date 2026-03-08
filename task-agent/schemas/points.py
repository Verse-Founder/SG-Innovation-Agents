"""
schemas/points.py
积分系统 Pydantic v2 模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PointsTransaction(BaseModel):
    """积分变动记录"""
    user_id: str
    amount: int
    reason: str = ""
    task_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    transaction_type: str = "earn"  # earn / spend / steal / bonus


class PointsBalance(BaseModel):
    """用户积分余额"""
    user_id: str
    total_earned: int = 0
    total_spent: int = 0
    current_balance: int = 0
    streak_days: int = 0  # 连续完成天数
    streak_multiplier: float = 1.0


class EnergyStealEvent(BaseModel):
    """偷能量事件（预留）"""
    stealer_id: str
    target_id: str
    amount: int = 1
    timestamp: datetime = Field(default_factory=datetime.now)
    group_id: Optional[str] = None
