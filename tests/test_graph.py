"""
tests/test_graph.py
端到端 LangGraph 流程测试（使用规则引擎回退，不调用真实 LLM）
"""
import pytest
from unittest.mock import patch, MagicMock
from graph.builder import run_task_agent


def _mock_sealion_return_fallback(*args, **kwargs):
    """Mock SEA-LION：返回无效 JSON 让引擎自动回退到规则模式"""
    return "NOT_VALID_JSON_WILL_TRIGGER_FALLBACK"


class TestGraphE2E:

    @patch("utils.llm_factory.requests.post")
    def test_system_trigger(self, mock_post):
        """系统触发 → 应生成任务"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "NOT_VALID_JSON"}}]
        }
        mock_post.return_value = mock_resp

        output = run_task_agent("user_001", trigger_source="system")
        assert output is not None
        batch = output.get("batch", {})
        assert batch.get("user_id") == "user_001"

    @patch("utils.llm_factory.requests.post")
    def test_chatbot_trigger(self, mock_post):
        """chatbot 触发"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "NOT_VALID_JSON"}}]
        }
        mock_post.return_value = mock_resp

        output = run_task_agent(
            "user_001",
            trigger_source="chatbot",
            trigger_payload={"type": "task_request", "request": "给我推荐今天的任务"},
        )
        assert output is not None
        assert "risk_level" in output

    @patch("utils.llm_factory.requests.post")
    def test_alert_trigger(self, mock_post):
        """预警 Agent 触发"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "NOT_VALID_JSON"}}]
        }
        mock_post.return_value = mock_resp

        output = run_task_agent(
            "user_001",
            trigger_source="alert_agent",
            trigger_payload={"severity": "high", "alert_level": "high"},
        )
        assert output is not None
        assert output.get("risk_level") in ("high", "critical", "medium", "low")

    @patch("utils.llm_factory.requests.post")
    def test_output_has_notifications(self, mock_post):
        """输出应包含推送通知"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "NOT_VALID_JSON"}}]
        }
        mock_post.return_value = mock_resp

        output = run_task_agent("user_001", trigger_source="system")
        assert "notifications" in output

    @patch("utils.llm_factory.requests.post")
    def test_exercise_scenario(self, mock_post):
        """运动场景：chatbot 转发'我想跑步'"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "NOT_VALID_JSON"}}]
        }
        mock_post.return_value = mock_resp

        output = run_task_agent(
            "user_001",
            trigger_source="chatbot",
            trigger_payload={"type": "task_request", "request": "我打算去跑步"},
        )
        assert output is not None
        batch = output.get("batch", {})
        tasks = batch.get("tasks", [])
        # 运动前低血糖风险（mock 数据中血糖 4.2）→ 应有饮食提醒
        diet_tasks = [t for t in tasks if t.get("category") == "diet"]
        assert len(diet_tasks) >= 1

    @patch("utils.llm_factory.requests.post")
    def test_renal_scenario(self, mock_post):
        """肾功能场景"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "NOT_VALID_JSON"}}]
        }
        mock_post.return_value = mock_resp

        output = run_task_agent(
            "user_001",
            trigger_source="system",
            trigger_payload={"request": "肾功能检查"},
        )
        assert output is not None
        assert output.get("renal_concern") is True
