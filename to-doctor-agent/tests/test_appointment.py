"""
tests/test_appointment.py
预约建议测试
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.appointment_advisor import generate_appointment_suggestions


class TestAppointmentAdvisor:
    def test_routine_always_present(self):
        analysis = {"glucose_trend": {}, "egfr_trend": {}, "medication_adherence": {}}
        suggestions = generate_appointment_suggestions(analysis)
        departments = [s["department"] for s in suggestions]
        assert "内分泌科" in departments

    def test_egfr_declining_triggers_nephrology(self):
        analysis = {
            "glucose_trend": {},
            "egfr_trend": {"declining": True, "latest": 55, "ckd_stage": "G3a"},
            "medication_adherence": {},
        }
        suggestions = generate_appointment_suggestions(analysis)
        departments = [s["department"] for s in suggestions]
        assert "肾内科" in departments

    def test_egfr_severe_is_urgent(self):
        analysis = {
            "glucose_trend": {},
            "egfr_trend": {"declining": True, "latest": 25, "ckd_stage": "G4"},
            "medication_adherence": {},
        }
        suggestions = generate_appointment_suggestions(analysis)
        nephrology = [s for s in suggestions if s["department"] == "肾内科"]
        assert nephrology[0]["urgency"] == "urgent"

    def test_high_glucose_triggers_endocrinology(self):
        analysis = {
            "glucose_trend": {
                "status": "analyzed", "average": 11.0,
                "high_count": 8, "total_readings": 10,
            },
            "egfr_trend": {},
            "medication_adherence": {},
        }
        suggestions = generate_appointment_suggestions(analysis)
        endocrinology = [s for s in suggestions if "内分泌" in s["department"]]
        assert len(endocrinology) >= 1

    def test_dawn_phenomenon(self):
        analysis = {
            "glucose_trend": {"status": "analyzed", "dawn_phenomenon": True, "fasting_average": 8.5,
                              "average": 7.0, "high_count": 2, "total_readings": 10},
            "egfr_trend": {},
            "medication_adherence": {},
        }
        suggestions = generate_appointment_suggestions(analysis)
        dawn = [s for s in suggestions if "黎明" in s.get("reason", "")]
        assert len(dawn) >= 1

    def test_low_adherence(self):
        analysis = {
            "glucose_trend": {},
            "egfr_trend": {},
            "medication_adherence": {"status": "analyzed", "latest_pct": 55.0},
        }
        suggestions = generate_appointment_suggestions(analysis)
        adherence = [s for s in suggestions if "依从性" in s.get("reason", "")]
        assert len(adherence) >= 1

    def test_suggested_date_is_weekday(self):
        analysis = {"glucose_trend": {}, "egfr_trend": {}, "medication_adherence": {}}
        suggestions = generate_appointment_suggestions(analysis)
        from datetime import datetime
        for s in suggestions:
            if s.get("suggested_date"):
                date = datetime.strptime(s["suggested_date"], "%Y-%m-%d")
                assert date.weekday() < 5  # Monday-Friday
