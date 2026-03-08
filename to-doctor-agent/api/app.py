"""
api/app.py
FastAPI 应用 — To-Doctor Agent
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时创建表，关闭时清理"""
    from db.session import create_all_tables
    await create_all_tables()
    logger.info("✅ To-Doctor Agent 数据库表已就绪")
    yield
    logger.info("🛑 To-Doctor Agent 关闭")


app = FastAPI(
    title="To-Doctor Agent | 医生端健康报告系统",
    description="SG Innovation Challenge — 患者数据 → 结构化医疗报告 → 医生端",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes import router
app.include_router(router, prefix="/api/v1")
