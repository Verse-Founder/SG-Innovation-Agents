"""
tests/test_points_engine.py
测试积分引擎
"""
import pytest
from engine.points_engine import calculate_task_points, process_task_completion
from schemas.points import PointsBalance


class TestCalculatePoints:

    def test_basic_exercise_points(self):
        pts = calculate_task_points("exercise", "daily_routine", streak_days=0)
        assert pts == 10  # settings.POINTS_DAILY_EXERCISE

    def test_meal_photo_points(self):
        pts = calculate_task_points("diet", "daily_routine", streak_days=0)
        assert pts == 5

    def test_medication_points(self):
        pts = calculate_task_points("medication", "daily_routine", streak_days=0)
        assert pts == 10

    def test_weekly_bonus(self):
        base = calculate_task_points("exercise", "daily_routine", streak_days=0)
        weekly = calculate_task_points("exercise", "weekly_personalized", streak_days=0)
        assert weekly > base

    def test_streak_multiplier(self):
        no_streak = calculate_task_points("exercise", "daily_routine", streak_days=0)
        with_streak = calculate_task_points("exercise", "daily_routine", streak_days=5)
        assert with_streak > no_streak


class TestProcessCompletion:

    def test_basic_completion(self, empty_balance):
        tx, balance = process_task_completion(
            "user_001", "task_001", "exercise", "daily_routine", empty_balance
        )
        assert tx.amount > 0
        assert balance.current_balance == tx.amount
        assert balance.streak_days == 1

    def test_streak_accumulation(self, streak_balance):
        tx, balance = process_task_completion(
            "user_001", "task_002", "diet", "daily_routine", streak_balance
        )
        assert balance.streak_days == 6
        assert balance.current_balance > streak_balance.current_balance
