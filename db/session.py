"""
db/session.py
AsyncSession 工厂 + 连接池
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
    """创建所有表"""
    from db.models import Base
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables():
    """删除所有表"""
    from db.models import Base
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def get_engine():
    return _engine
