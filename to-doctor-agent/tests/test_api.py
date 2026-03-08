"""
tests/test_api.py
FastAPI 路由测试
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.app import app


def _mock_llm_post():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "mock risk summary"}}]
    }
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


class TestHealthEndpoint:
    def test_health(self):
        with TestClient(app) as client:
            resp = client.get("/api/v1/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"


class TestReportEndpoints:
    @patch("utils.llm_factory.requests.post")
    def test_generate_report(self, mock_post):
        mock_post.return_value = _mock_llm_post()
        with TestClient(app) as client:
            resp = client.post("/api/v1/reports/generate", json={
                "user_id": "test_patient", "days": 30,
            })
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["status"] == "completed"
            assert data["summary"]

    @patch("utils.llm_factory.requests.post")
    def test_idempotent_generate(self, mock_post):
        mock_post.return_value = _mock_llm_post()
        with TestClient(app) as client:
            r1 = client.post("/api/v1/reports/generate", json={
                "user_id": "test", "request_id": "idem-001",
            })
            r2 = client.post("/api/v1/reports/generate", json={
                "user_id": "test", "request_id": "idem-001",
            })
            assert r1.json()["data"]["report_id"] == r2.json()["data"]["report_id"]

    @patch("utils.llm_factory.requests.post")
    def test_get_user_reports(self, mock_post):
        mock_post.return_value = _mock_llm_post()
        with TestClient(app) as client:
            client.post("/api/v1/reports/generate", json={"user_id": "lister"})
            resp = client.get("/api/v1/reports/user/lister")
            assert resp.status_code == 200
            assert len(resp.json()["data"]) >= 1


class TestAuthEndpoints:
    def test_auth_request(self):
        with TestClient(app) as client:
            resp = client.post("/api/v1/auth/request", json={
                "doctor_id": "dr1", "patient_id": "p1", "reason": "复诊",
            })
            assert resp.status_code == 200
            assert resp.json()["data"]["status"] == "pending"

    def test_auth_grant(self):
        with TestClient(app) as client:
            r1 = client.post("/api/v1/auth/request", json={
                "doctor_id": "dr1", "patient_id": "p1",
            })
            auth_id = r1.json()["data"]["auth_id"]
            r2 = client.post("/api/v1/auth/grant", json={
                "auth_id": auth_id, "patient_id": "p1", "granted": True,
            })
            assert r2.json()["data"]["status"] == "granted"

    def test_pending_list(self):
        with TestClient(app) as client:
            client.post("/api/v1/auth/request", json={
                "doctor_id": "dr1", "patient_id": "p_pending",
            })
            resp = client.get("/api/v1/auth/pending/p_pending")
            assert resp.status_code == 200
            assert len(resp.json()["data"]) >= 1


class TestPrescriptionEndpoints:
    def test_create_prescription(self):
        with TestClient(app) as client:
            resp = client.post("/api/v1/prescriptions", json={
                "patient_id": "p1", "doctor_id": "dr1",
                "medication_name": "Metformin", "dosage": "500mg",
                "frequency": "每日两次",
            })
            assert resp.status_code == 200
            assert resp.json()["data"]["prescription_id"]

    def test_invalid_prescription(self):
        with TestClient(app) as client:
            resp = client.post("/api/v1/prescriptions", json={
                "patient_id": "p1", "doctor_id": "dr1",
                "medication_name": "", "dosage": "500mg",
                "frequency": "daily",
            })
            assert resp.status_code == 400
