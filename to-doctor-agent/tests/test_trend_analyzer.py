"""
tests/test_trend_analyzer.py
趋势分析引擎测试
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.trend_analyzer import (
    analyze_glucose_trend, analyze_egfr_trend,
    analyze_medication_adherence, analyze_activity_trend,
    analyze_task_completion, generate_full_trend_analysis,
)

# ── 血糖分析 ─────────────────────────────────────────────

class TestGlucoseTrend:
    def test_no_data(self):
        result = analyze_glucose_trend([])
        assert result["status"] == "no_data"

    def test_basic_analysis(self):
        logs = [
            {"blood_glucose": 6.0, "glucose_context": "fasting"},
            {"blood_glucose": 8.5, "glucose_context": "postprandial"},
            {"blood_glucose": 5.5, "glucose_context": "fasting"},
        ]
        result = analyze_glucose_trend(logs)
        assert result["status"] == "analyzed"
        assert result["total_readings"] == 3
        assert 5.0 < result["average"] < 8.0

    def test_dawn_phenomenon(self):
        logs = [
            {"blood_glucose": 8.0, "glucose_context": "fasting"},
            {"blood_glucose": 7.5, "glucose_context": "fasting"},
            {"blood_glucose": 9.0, "glucose_context": "fasting"},
        ]
        result = analyze_glucose_trend(logs)
        assert result["dawn_phenomenon"] is True

    def test_high_low_count(self):
        logs = [
            {"blood_glucose": 3.0},
            {"blood_glucose": 12.0},
            {"blood_glucose": 6.0},
        ]
        result = analyze_glucose_trend(logs)
        assert result["high_count"] == 1
        assert result["low_count"] == 1


# ── eGFR 分析 ────────────────────────────────────────────

class TestEgfrTrend:
    def test_no_data(self):
        result = analyze_egfr_trend([])
        assert result["status"] == "no_data"

    def test_normal_egfr(self):
        logs = [{"egfr": 95.0}, {"egfr": 92.0}]
        result = analyze_egfr_trend(logs)
        assert result["ckd_stage"] == "G1"

    def test_declining_trend(self):
        logs = [{"egfr": 80.0}, {"egfr": 70.0}, {"egfr": 60.0}]
        result = analyze_egfr_trend(logs)
        assert result["declining"] is True

    def test_stage_g3b(self):
        logs = [{"egfr": 40.0}]
        result = analyze_egfr_trend(logs)
        assert result["ckd_stage"] == "G3b"

    def test_stage_g3a(self):
        logs = [{"egfr": 50.0}]
        result = analyze_egfr_trend(logs)
        assert result["ckd_stage"] == "G3a"


# ── 用药依从性 ───────────────────────────────────────────

class TestMedicationAdherence:
    def test_no_data(self):
        result = analyze_medication_adherence([])
        assert result["status"] == "no_data"

    def test_basic(self):
        patterns = [
            {"medication_adherence_pct": 90.0},
            {"medication_adherence_pct": 85.0},
        ]
        result = analyze_medication_adherence(patterns)
        assert result["status"] == "analyzed"
        assert result["latest_pct"] == 90.0

    def test_trend_improving(self):
        patterns = [
            {"medication_adherence_pct": 95.0},
            {"medication_adherence_pct": 80.0},
        ]
        result = analyze_medication_adherence(patterns)
        assert result["trend"] == "improving"


# ── 运动分析 ─────────────────────────────────────────────

class TestActivityTrend:
    def test_no_data(self):
        result = analyze_activity_trend([], [])
        assert result["status"] == "no_data"

    def test_step_analysis(self):
        logs = [{"steps": 7000}, {"steps": 5000}, {"steps": 8000}]
        result = analyze_activity_trend(logs, [])
        assert result["status"] == "analyzed"
        assert result["goal_met_days"] == 2  # 7000 and 8000 >= 6000

    def test_fallback_to_behavior(self):
        result = analyze_activity_trend([], [{"avg_daily_steps": 5500}])
        assert result["status"] == "partial"


# ── 任务完成率 ───────────────────────────────────────────

class TestTaskCompletion:
    def test_no_data(self):
        result = analyze_task_completion({})
        assert result["status"] == "no_data"

    def test_basic(self):
        result = analyze_task_completion({"total_tasks": 20, "completed_tasks": 15})
        assert result["completion_rate"] == 75.0


# ── 完整分析 ─────────────────────────────────────────────

class TestFullAnalysis:
    def test_completeness_tracking(self):
        result = generate_full_trend_analysis([], [], {})
        assert result["is_complete"] is False
        assert result["data_completeness"]["glucose"] is False

    def test_with_data(self):
        logs = [{"blood_glucose": 6.5, "glucose_context": "fasting", "steps": 7000}]
        patterns = [{"medication_adherence_pct": 90.0}]
        tasks = {"total_tasks": 10, "completed_tasks": 8}
        result = generate_full_trend_analysis(logs, patterns, tasks)
        assert result["glucose_trend"]["status"] == "analyzed"
        assert result["medication_adherence"]["status"] == "analyzed"
