"""
tests/test_db.py
数据库 CRUD 测试 — in-memory SQLite
pytest-asyncio auto mode
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from db.models import Base
from db import crud

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(TEST_DB_URL, echo=False)
_test_session_factory = async_sessionmaker(
    _engine, class_=AsyncSession, expire_on_commit=False,
)


@pytest.fixture(autouse=True)
async def setup_db():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session():
    async with _test_session_factory() as s:
        yield s


class TestTaskCRUD:

    async def test_create_task(self, session):
        task = await crud.create_task(
            session, user_id="u1", title="测试步数打卡",
            category="exercise", description="目标6000步", points=10,
        )
        assert task.id is not None
        assert task.user_id == "u1"
        assert task.title == "测试步数打卡"
        assert task.points == 10
        assert task.status == "pending"

    async def test_get_user_tasks(self, session):
        await crud.create_task(session, user_id="u2", title="任务A", category="diet")
        await crud.create_task(session, user_id="u2", title="任务B", category="exercise")
        await crud.create_task(session, user_id="other", title="任务C", category="quiz")
        await session.flush()
        tasks = await crud.get_user_tasks(session, "u2")
        assert len(tasks) == 2

    async def test_filter_status(self, session):
        t = await crud.create_task(session, user_id="u3", title="已完成", category="monitoring")
        t.status = "completed"
        await session.flush()
        await crud.create_task(session, user_id="u3", title="待办", category="monitoring")
        await session.flush()
        pending = await crud.get_user_tasks(session, "u3", status="pending")
        assert len(pending) == 1
        assert pending[0].title == "待办"

    async def test_complete_task(self, session):
        task = await crud.create_task(
            session, user_id="u4", title="完成测试", category="exercise", points=15,
        )
        await session.flush()
        completion = await crud.complete_task(session, task.id, "u4")
        assert completion is not None
        assert completion.points_earned == 15

    async def test_complete_wrong_user(self, session):
        task = await crud.create_task(session, user_id="uA", title="A的", category="diet")
        await session.flush()
        assert await crud.complete_task(session, task.id, "uB") is None

    async def test_complete_nonexistent(self, session):
        assert await crud.complete_task(session, "fake-id", "uA") is None


class TestPointsCRUD:

    async def test_add_points(self, session):
        entry = await crud.add_points_transaction(
            session, user_id="p1", amount=10, reason="测试",
        )
        assert entry.amount == 10

    async def test_balance(self, session):
        await crud.add_points_transaction(session, user_id="p2", amount=20, reason="r1")
        await crud.add_points_transaction(session, user_id="p2", amount=15, reason="r2")
        await crud.add_points_transaction(
            session, user_id="p2", amount=5, reason="消费", transaction_type="spend",
        )
        await session.flush()
        bal = await crud.get_points_balance(session, "p2")
        assert bal["total_earned"] == 35
        assert bal["total_spent"] == 5
        assert bal["current_balance"] == 30

    async def test_empty_balance(self, session):
        bal = await crud.get_points_balance(session, "nobody")
        assert bal["current_balance"] == 0


class TestHealthCRUD:

    async def test_create_log(self, session):
        log = await crud.create_health_log(
            session, user_id="h1", blood_glucose=6.5, glucose_context="fasting",
        )
        assert log.blood_glucose == 6.5

    async def test_recent_logs(self, session):
        await crud.create_health_log(session, user_id="h2", blood_glucose=5.5)
        await crud.create_health_log(session, user_id="h2", steps=4500)
        await session.flush()
        logs = await crud.get_recent_health_logs(session, "h2")
        assert len(logs) == 2


class TestMiscCRUD:

    async def test_chat_insight(self, session):
        ci = await crud.create_chat_insight(
            session, user_id="c1", insight_type="meal", content="吃了鸡饭",
        )
        assert ci.insight_type == "meal"

    async def test_behavior_pattern(self, session):
        bp = await crud.create_behavior_pattern(
            session, user_id="b1", avg_daily_steps=5000,
            medication_adherence_pct=90.0, task_completion_rate=0.8,
        )
        assert bp.avg_daily_steps == 5000
