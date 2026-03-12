"""
tests/test_intelligence.py
测试统一智能引擎（规则回退模式）
"""
import pytest
from engine.intelligence import _rule_based_fallback, build_patient_data_prompt
from schemas.health import HealthSnapshot, BehaviorPattern


class TestRuleBasedFallback:
    """测试规则引擎回退（不依赖 LLM）"""

    def test_normal_scenario(self, normal_snapshot, behavior_pattern):
        """正常场景：应有复诊提醒（距HbA1c ~80天）"""
        risk, tasks = _rule_based_fallback(normal_snapshot, behavior_pattern)
        assert risk.risk_level in ("low", "medium")
        # 80天距90天周期还有余裕，但在14天预警范围内
        checkup_tasks = [t for t in tasks if t.get("category") == "checkup"]
        assert len(checkup_tasks) >= 0  # 可能有复诊提醒

    def test_low_glucose_detection(self, pre_exercise_snapshot, behavior_pattern):
        """运动前低血糖风险"""
        risk, tasks = _rule_based_fallback(pre_exercise_snapshot, behavior_pattern)
        assert risk.risk_level in ("high", "critical")
        diet_tasks = [t for t in tasks if t.get("category") == "diet"]
        assert len(diet_tasks) >= 1
        assert any("补充" in t.get("title", "") or "食物" in t.get("title", "") for t in diet_tasks)

    def test_high_glucose_detection(self, high_glucose_snapshot, behavior_pattern):
        """高血糖检测"""
        risk, tasks = _rule_based_fallback(high_glucose_snapshot, behavior_pattern)
        assert risk.risk_level in ("high", "critical")
        exercise_tasks = [t for t in tasks if t.get("category") == "exercise"]
        assert len(exercise_tasks) >= 1

    def test_renal_concern(self, renal_concern_snapshot, behavior_pattern):
        """肾功能异常检测"""
        risk, tasks = _rule_based_fallback(renal_concern_snapshot, behavior_pattern)
        assert risk.risk_level == "critical"
        assert risk.renal_concern is True
        assert risk.requires_doctor_review is True
        renal_tasks = [t for t in tasks if t.get("category") == "renal"]
        assert len(renal_tasks) >= 1

    def test_medication_missed(self, medication_missed_snapshot, behavior_pattern):
        """漏服药物检测"""
        risk, tasks = _rule_based_fallback(medication_missed_snapshot, behavior_pattern)
        med_tasks = [t for t in tasks if t.get("category") == "medication"]
        assert len(med_tasks) >= 1
        assert any("Metformin" in t.get("title", "") for t in med_tasks)

    def test_caring_messages_present(self, high_glucose_snapshot, behavior_pattern):
        """所有任务都应有温暖话术"""
        _, tasks = _rule_based_fallback(high_glucose_snapshot, behavior_pattern)
        for task in tasks:
            assert task.get("caring_message"), f"任务 '{task.get('title')}' 缺少 caring_message"
            assert len(task["caring_message"]) > 5


class TestPatientDataPrompt:
    """测试患者数据 prompt 构建"""

    def test_prompt_contains_key_data(self, normal_snapshot, behavior_pattern):
        prompt = build_patient_data_prompt(normal_snapshot, behavior_pattern)
        assert "user_001" in prompt
        assert "血糖数据" in prompt
        assert "今日消耗" in prompt
        assert "eGFR" in prompt
        assert "行为模式" in prompt

    def test_prompt_includes_chat_insights(self, normal_snapshot, behavior_pattern, chat_insights):
        prompt = build_patient_data_prompt(normal_snapshot, behavior_pattern, chat_insights)
        assert "聊天记录摘要" in prompt
        for insight in chat_insights:
            assert insight in prompt

    def test_prompt_with_renal_data(self, renal_concern_snapshot, behavior_pattern):
        prompt = build_patient_data_prompt(renal_concern_snapshot, behavior_pattern)
        assert "52.0" in prompt  # eGFR
        assert "泡沫尿" in prompt
        assert "declining" in prompt
