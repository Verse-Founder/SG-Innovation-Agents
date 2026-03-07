"""
tests/test_checkup_scheduler.py
测试智能复诊调度
"""
import pytest
from datetime import timedelta
from engine.checkup_scheduler import assess_checkup_needs, get_next_checkup_date
from schemas.health import HealthSnapshot, GlucosePattern, RenalIndicators
from utils.time_utils import now_sgt


class TestCheckupScheduler:

    def test_hba1c_overdue(self):
        """HbA1c 超期提醒"""
        snapshot = HealthSnapshot(
            user_id="test",
            last_hba1c_date=now_sgt() - timedelta(days=100),
        )
        recs = assess_checkup_needs(snapshot)
        hba1c_recs = [r for r in recs if "HbA1c" in r["type"]]
        assert len(hba1c_recs) >= 1
        assert hba1c_recs[0]["urgency"] == "high"

    def test_hba1c_upcoming(self):
        """HbA1c 即将到期"""
        snapshot = HealthSnapshot(
            user_id="test",
            last_hba1c_date=now_sgt() - timedelta(days=80),
        )
        recs = assess_checkup_needs(snapshot)
        hba1c_recs = [r for r in recs if "HbA1c" in r["type"]]
        assert len(hba1c_recs) >= 1
        assert hba1c_recs[0]["urgency"] == "medium"

    def test_worsening_glucose_triggers_early_checkup(self):
        """血糖恶化 → 提前复诊"""
        snapshot = HealthSnapshot(
            user_id="test",
            glucose=GlucosePattern(
                trend="worsening",
                avg_fasting=9.5,
            ),
            last_hba1c_date=now_sgt() - timedelta(days=30),
        )
        recs = assess_checkup_needs(snapshot)
        glucose_recs = [r for r in recs if "血糖" in r["type"]]
        assert len(glucose_recs) >= 1
        assert glucose_recs[0]["urgency"] == "high"

    def test_declining_egfr_triggers_renal_checkup(self):
        """eGFR 下降 → 提前肾内科复诊"""
        snapshot = HealthSnapshot(
            user_id="test",
            renal=RenalIndicators(egfr=55.0, egfr_trend="declining"),
        )
        recs = assess_checkup_needs(snapshot)
        renal_recs = [r for r in recs if "肾功能" in r["type"]]
        assert len(renal_recs) >= 1
        assert renal_recs[0]["urgency"] in ("high", "critical")

    def test_low_medication_adherence(self):
        """低服药率 → 用药评估"""
        snapshot = HealthSnapshot(
            user_id="test",
            medication_adherence_pct=50.0,
        )
        recs = assess_checkup_needs(snapshot)
        med_recs = [r for r in recs if "用药" in r["type"]]
        assert len(med_recs) >= 1

    def test_dawn_phenomenon(self):
        """黎明现象 → 血糖模式复诊"""
        snapshot = HealthSnapshot(
            user_id="test",
            glucose=GlucosePattern(has_dawn_phenomenon=True),
        )
        recs = assess_checkup_needs(snapshot)
        dawn_recs = [r for r in recs if "模式" in r["type"] or "黎明" in r.get("reason", "")]
        assert len(dawn_recs) >= 1

    def test_caring_messages_in_recommendations(self):
        """所有复诊建议应有温暖话术"""
        snapshot = HealthSnapshot(
            user_id="test",
            last_hba1c_date=now_sgt() - timedelta(days=100),
            medication_adherence_pct=60.0,
        )
        recs = assess_checkup_needs(snapshot)
        for rec in recs:
            assert "caring_message" in rec
            assert len(rec["caring_message"]) > 10


class TestGetNextCheckupDate:

    def test_basic(self):
        from datetime import datetime
        d = datetime(2026, 1, 15)
        next_d = get_next_checkup_date(d, 3)
        assert next_d.month == 4
        assert next_d.year == 2026

    def test_year_wrap(self):
        from datetime import datetime
        d = datetime(2026, 11, 15)
        next_d = get_next_checkup_date(d, 3)
        assert next_d.month == 2
        assert next_d.year == 2027

    def test_none_input(self):
        assert get_next_checkup_date(None, 3) is None
