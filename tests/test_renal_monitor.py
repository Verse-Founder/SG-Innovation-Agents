"""
tests/test_renal_monitor.py
测试肾功能监测
"""
import pytest
from engine.renal_monitor import assess_renal_status, max_concern
from schemas.health import HealthSnapshot, RenalIndicators
from utils.time_utils import now_sgt
from datetime import timedelta


class TestRenalMonitor:

    def test_normal_egfr(self, normal_snapshot):
        """正常 eGFR 不应有 concern"""
        result = assess_renal_status(normal_snapshot)
        assert result["concern_level"] in ("none", "watch")
        assert len(result["findings"]) <= 1

    def test_severe_egfr_decline(self, renal_concern_snapshot):
        """eGFR < 60：warning/critical"""
        result = assess_renal_status(renal_concern_snapshot)
        assert result["concern_level"] in ("warning", "critical")
        assert len(result["findings"]) >= 1
        assert any("eGFR" in f for f in result["findings"])

    def test_foam_urine_detection(self):
        """泡沫尿检测"""
        snapshot = HealthSnapshot(
            user_id="test",
            renal=RenalIndicators(has_foam_urine=True, egfr=80.0),
        )
        result = assess_renal_status(snapshot)
        assert result["concern_level"] != "none"
        assert any("泡沫尿" in f for f in result["findings"])

    def test_proteinuria_detection(self):
        """蛋白尿检测"""
        snapshot = HealthSnapshot(
            user_id="test",
            renal=RenalIndicators(proteinuria=150.0, egfr=75.0),
        )
        result = assess_renal_status(snapshot)
        assert result["concern_level"] != "none"
        assert any("蛋白尿" in f for f in result["findings"])

    def test_egfr_decline_trend(self):
        """eGFR 下降趋势警报"""
        snapshot = HealthSnapshot(
            user_id="test",
            renal=RenalIndicators(egfr=70.0, egfr_previous=80.0, egfr_trend="declining"),
        )
        result = assess_renal_status(snapshot)
        assert any("下降" in f for f in result["findings"])

    def test_symptom_correlation(self):
        """症状关联检测"""
        snapshot = HealthSnapshot(
            user_id="test",
            reported_symptoms=["口干", "容易疲劳"],
            renal=RenalIndicators(egfr=90.0),
        )
        result = assess_renal_status(snapshot)
        assert result["concern_level"] != "none"
        assert any("症状" in f for f in result["findings"])

    def test_kidney_failure_level(self):
        """严重肾衰竭"""
        snapshot = HealthSnapshot(
            user_id="test",
            renal=RenalIndicators(egfr=12.0),
        )
        result = assess_renal_status(snapshot)
        assert result["concern_level"] == "critical"
        assert "紧急就医" in result["recommendations"]


class TestMaxConcern:
    def test_upgrades(self):
        assert max_concern("none", "watch") == "watch"
        assert max_concern("watch", "warning") == "warning"
        assert max_concern("warning", "critical") == "critical"

    def test_no_downgrade(self):
        assert max_concern("critical", "low") == "critical"
        assert max_concern("warning", "none") == "warning"
