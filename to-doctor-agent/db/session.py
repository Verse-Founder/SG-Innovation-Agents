"""
db/session.py
AsyncSession 工厂 — 与 task-agent 共享 DB_URL
"""
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import settings

_engine = create_async_engine(
    settings.DB_URL,
    echo=settings.IS_DEV,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session():
    """获取 async 数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_all_tables():
    """创建 to-doctor-agent 新增表"""
    from db.models import DoctorBase
    async with _engine.begin() as conn:
        await conn.run_sync(DoctorBase.metadata.create_all)


async def drop_all_tables():
    """删除 to-doctor-agent 新增表"""
    from db.models import DoctorBase
    async with _engine.begin() as conn:
        await conn.run_sync(DoctorBase.metadata.drop_all)
