"""
tests/test_db.py
数据库 CRUD 测试 — in-memory SQLite
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from db.models import DoctorBase
from db import crud

_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
_test_session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

pytestmark = pytest.mark.asyncio(loop_scope="module")


@pytest.fixture(autouse=True)
async def setup_db():
    async with _engine.begin() as conn:
        await conn.run_sync(DoctorBase.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(DoctorBase.metadata.drop_all)


@pytest.fixture
async def session():
    async with _test_session_factory() as s:
        yield s


class TestReportCRUD:
    async def test_create_report(self, session):
        report = await crud.create_report(session, user_id="u1")
        assert report.id is not None
        assert report.status == "generating"

    async def test_idempotent_create(self, session):
        r1 = await crud.create_report(session, user_id="u1", request_id="req-001")
        r2 = await crud.create_report(session, user_id="u1", request_id="req-001")
        assert r1.id == r2.id  # 同一个 request_id 返回同一个

    async def test_update_content(self, session):
        report = await crud.create_report(session, user_id="u1")
        await session.flush()
        updated = await crud.update_report_content(
            session, report.id, data_json={"test": 1}, summary="测试摘要",
        )
        assert updated.status == "completed"
        assert updated.summary == "测试摘要"

    async def test_get_user_reports(self, session):
        await crud.create_report(session, user_id="u2")
        await crud.create_report(session, user_id="u2")
        await crud.create_report(session, user_id="other")
        await session.flush()
        reports = await crud.get_user_reports(session, "u2")
        assert len(reports) == 2


class TestAuthCRUD:
    async def test_create_auth_request(self, session):
        auth = await crud.create_auth_request(session, doctor_id="dr1", patient_id="p1")
        assert auth.status == "pending"

    async def test_grant_authorization(self, session):
        auth = await crud.create_auth_request(session, doctor_id="dr1", patient_id="p1")
        await session.flush()
        granted = await crud.grant_authorization(session, auth.id, "p1", True)
        assert granted.status == "granted"
        assert granted.expires_at is not None

    async def test_deny_authorization(self, session):
        auth = await crud.create_auth_request(session, doctor_id="dr1", patient_id="p1")
        await session.flush()
        denied = await crud.grant_authorization(session, auth.id, "p1", False)
        assert denied.status == "denied"

    async def test_wrong_patient_cant_grant(self, session):
        auth = await crud.create_auth_request(session, doctor_id="dr1", patient_id="p1")
        await session.flush()
        result = await crud.grant_authorization(session, auth.id, "wrong_patient", True)
        assert result is None

    async def test_check_access(self, session):
        auth = await crud.create_auth_request(session, doctor_id="dr1", patient_id="p1")
        await session.flush()
        assert await crud.check_doctor_access(session, "dr1", "p1") is False
        await crud.grant_authorization(session, auth.id, "p1", True)
        await session.flush()
        assert await crud.check_doctor_access(session, "dr1", "p1") is True

    async def test_pending_list(self, session):
        await crud.create_auth_request(session, doctor_id="dr1", patient_id="p1")
        await crud.create_auth_request(session, doctor_id="dr2", patient_id="p1")
        await session.flush()
        pending = await crud.get_pending_authorizations(session, "p1")
        assert len(pending) == 2


class TestPrescriptionCRUD:
    async def test_create_prescription(self, session):
        rx = await crud.create_prescription(
            session, patient_id="p1", doctor_id="dr1",
            medication_name="Metformin", dosage="500mg", frequency="每日两次",
        )
        assert rx.id is not None
        assert rx.is_active is True

    async def test_get_prescriptions(self, session):
        await crud.create_prescription(
            session, patient_id="p2", doctor_id="dr1",
            medication_name="A", dosage="10mg", frequency="daily",
        )
        await session.flush()
        rxs = await crud.get_patient_prescriptions(session, "p2")
        assert len(rxs) == 1


class TestAuditCRUD:
    async def test_log_audit(self, session):
        entry = await crud.log_audit(
            session, action="report_generated",
            actor_id="p1", actor_type="patient", target_id="rpt1",
        )
        assert entry.action == "report_generated"
