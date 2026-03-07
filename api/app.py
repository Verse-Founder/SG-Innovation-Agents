"""
api/app.py
FastAPI 应用（对标 Julia 的 diabetes-guardian）
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时创建表，关闭时清理"""
    from db.session import create_all_tables
    await create_all_tables()
    logger.info("✅ 数据库表已就绪")
    yield
    logger.info("🛑 Task Agent 关闭")


app = FastAPI(
    title="Task Agent | 糖尿病健康任务管理",
    description="SG Innovation Challenge — 个性化任务发布Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "task-agent"}
