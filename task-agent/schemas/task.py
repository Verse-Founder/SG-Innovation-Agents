"""
schemas/task.py
任务相关的 Pydantic v2 数据模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class TaskType(str, Enum):
    DAILY_ROUTINE = "daily_routine"
    WEEKLY_PERSONALIZED = "weekly_personalized"
    DYNAMIC_RISK = "dynamic_risk"
    DOCTOR_ASSIGNED = "doctor_assigned"


class TaskCategory(str, Enum):
    EXERCISE = "exercise"
    DIET = "diet"
    MEDICATION = "medication"
    MONITORING = "monitoring"
    QUIZ = "quiz"
    CHECKUP = "checkup"
    RENAL = "renal"


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    SKIPPED = "skipped"


class TaskCreate(BaseModel):
    """任务创建请求"""
    task_type: TaskType
    category: TaskCategory
    title: str
    description: str
    caring_message: str = Field(default="", description="温暖关怀的提示语")
    points: int = Field(default=5, ge=0)
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    user_id: str
    task_type: TaskType
    category: TaskCategory
    title: str
    description: str
    caring_message: str = ""
    points: int = 5
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)


class TaskBatch(BaseModel):
    """一批任务（周常/日常）"""
    user_id: str
    batch_type: str = "weekly"  # daily / weekly
    tasks: list[TaskResponse] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)
    summary: str = ""  # 本批次总结语


class RiskAssessment(BaseModel):
    """风险评估结果"""
    risk_level: str = "low"  # critical / high / medium / low
    risks: list[dict] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    requires_doctor_review: bool = False
    renal_concern: bool = False
    checkup_recommendation: Optional[str] = None
