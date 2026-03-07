"""
tests/test_api.py
FastAPI 路由测试
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.app import app


def _mock_llm_post():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "NOT_VALID_JSON"}}]
    }
    return mock_resp


class TestHealthEndpoint:
    def test_health_check(self):
        with TestClient(app) as client:
            resp = client.get("/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"


class TestTriggerEndpoints:
    @patch("utils.llm_factory.requests.post")
    def test_chatbot(self, mock_post):
        mock_post.return_value = _mock_llm_post()
        with TestClient(app) as client:
            resp = client.post("/api/v1/trigger/chatbot", json={
                "user_id": "test", "payload": {"type": "task_request", "request": "推荐任务"},
            })
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"

    @patch("utils.llm_factory.requests.post")
    def test_alert(self, mock_post):
        mock_post.return_value = _mock_llm_post()
        with TestClient(app) as client:
            resp = client.post("/api/v1/trigger/alert", json={
                "user_id": "test", "payload": {"severity": "high"},
            })
            assert resp.status_code == 200

    @patch("utils.llm_factory.requests.post")
    def test_doctor(self, mock_post):
        mock_post.return_value = _mock_llm_post()
        with TestClient(app) as client:
            resp = client.post("/api/v1/trigger/doctor", json={"user_id": "test"})
            assert resp.status_code == 200


class TestPointsEndpoint:
    def test_empty_balance(self):
        with TestClient(app) as client:
            resp = client.get("/api/v1/points/nobody")
            assert resp.status_code == 200
            assert resp.json()["data"]["current_balance"] == 0
