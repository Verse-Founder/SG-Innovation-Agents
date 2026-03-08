"""
tests/test_report_engine.py
报告生成引擎测试
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.report_generator import generate_report_data, generate_report_summary


def _make_health_logs():
    return [
        {"blood_glucose": 6.5, "glucose_context": "fasting", "steps": 7000, "egfr": 85.0},
        {"blood_glucose": 8.0, "glucose_context": "postprandial", "steps": 5000},
        {"blood_glucose": 5.5, "glucose_context": "fasting", "steps": 6500},
    ]

def _make_behavior():
    return [{"medication_adherence_pct": 88.0, "avg_daily_steps": 6200}]

def _make_tasks():
    return {"total_tasks": 30, "completed_tasks": 24, "streak_days": 5}


class TestReportData:
    def test_has_all_sections(self):
        data = generate_report_data("u1", _make_health_logs(), _make_behavior(), _make_tasks())
        assert "report_metadata" in data
        assert "glucose_analysis" in data
        assert "renal_function" in data
        assert "medication_adherence" in data
        assert "activity_summary" in data
        assert "appointment_suggestions" in data

    def test_patient_id(self):
        data = generate_report_data("u1", _make_health_logs(), _make_behavior(), _make_tasks())
        assert data["report_metadata"]["patient_id"] == "u1"

    def test_completeness_tracked(self):
        data = generate_report_data("u1", _make_health_logs(), _make_behavior(), _make_tasks())
        assert "data_completeness" in data["report_metadata"]

    def test_empty_data_no_crash(self):
        data = generate_report_data("u1", [], [], {})
        assert data["report_metadata"]["is_data_complete"] is False

    def test_appointments_generated(self):
        data = generate_report_data("u1", _make_health_logs(), _make_behavior(), _make_tasks())
        assert isinstance(data["appointment_suggestions"], list)
        assert len(data["appointment_suggestions"]) >= 1  # at least routine


class TestReportSummary:
    def test_summary_not_empty(self):
        data = generate_report_data("u1", _make_health_logs(), _make_behavior(), _make_tasks())
        summary = generate_report_summary(data)
        assert len(summary) > 50

    def test_summary_has_sections(self):
        data = generate_report_data("u1", _make_health_logs(), _make_behavior(), _make_tasks())
        summary = generate_report_summary(data)
        assert "血糖" in summary
        assert "肾功能" in summary

    def test_summary_with_no_data(self):
        data = generate_report_data("u1", [], [], {})
        summary = generate_report_summary(data)
        assert "数据不完整" in summary

    def test_incomplete_sections_flagged(self):
        data = generate_report_data("u1", [], _make_behavior(), _make_tasks())
        summary = generate_report_summary(data)
        assert "血糖" in summary  # should mention incomplete
