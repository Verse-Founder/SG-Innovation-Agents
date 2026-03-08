"""
tests/test_prescription.py
处方管理测试
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.prescription_manager import (
    validate_prescription, format_prescription_for_task_agent,
)


class TestPrescriptionValidation:
    def test_valid_prescription(self):
        result = validate_prescription("Metformin", "500mg", "twice daily")
        assert result["valid"] is True

    def test_empty_medication(self):
        result = validate_prescription("", "500mg", "daily")
        assert result["valid"] is False

    def test_empty_dosage(self):
        result = validate_prescription("Metformin", "", "daily")
        assert result["valid"] is False

    def test_known_drug_has_warnings(self):
        result = validate_prescription("metformin", "500mg", "daily")
        assert len(result.get("warnings", [])) >= 1


class TestTaskAgentPayload:
    def test_format(self):
        payload = format_prescription_for_task_agent(
            "p1", "Metformin", "500mg", "daily", "dr1"
        )
        assert payload["user_id"] == "p1"
        assert payload["trigger_source"] == "doctor"
        assert payload["payload"]["type"] == "prescription"
        assert payload["payload"]["medication_name"] == "Metformin"
