"""
tests/conftest.py
共享 pytest fixtures
"""
import pytest
import sys
import os

# 确保项目根目录在 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas.health import HealthSnapshot, BehaviorPattern
from schemas.points import PointsBalance
from utils.mock_data import (
    get_mock_user_profile,
    get_mock_health_snapshot,
    get_mock_behavior_pattern,
    get_mock_chat_insights,
)


@pytest.fixture
def user_profile():
    return get_mock_user_profile("user_001")


@pytest.fixture
def normal_snapshot():
    return get_mock_health_snapshot("user_001", "normal")


@pytest.fixture
def pre_exercise_snapshot():
    return get_mock_health_snapshot("user_001", "pre_exercise_risk")


@pytest.fixture
def high_glucose_snapshot():
    return get_mock_health_snapshot("user_001", "high_glucose")


@pytest.fixture
def renal_concern_snapshot():
    return get_mock_health_snapshot("user_001", "renal_concern")


@pytest.fixture
def medication_missed_snapshot():
    return get_mock_health_snapshot("user_001", "medication_missed")


@pytest.fixture
def behavior_pattern():
    return get_mock_behavior_pattern("user_001")


@pytest.fixture
def chat_insights():
    return get_mock_chat_insights("normal")


@pytest.fixture
def empty_balance():
    return PointsBalance(user_id="user_001")


@pytest.fixture
def streak_balance():
    return PointsBalance(
        user_id="user_001",
        total_earned=100,
        current_balance=80,
        streak_days=5,
        streak_multiplier=1.5,
    )
