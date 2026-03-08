"""
tests/test_scheduler.py
定时任务测试 — 纯逻辑测试（不需要 Redis/Celery）
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduler.daily_routine import (
    generate_daily_tasks,
    generate_meal_photo_task,
    generate_daily_quiz,
    generate_hba1c_reminder,
    QUIZ_BANK,
)


class TestDailyTasks:
    def test_count(self):
        assert len(generate_daily_tasks("u1")) == 3

    def test_categories(self):
        cats = {t["category"] for t in generate_daily_tasks("u1")}
        assert cats == {"exercise", "monitoring", "medication"}

    def test_caring_message(self):
        for t in generate_daily_tasks("u1"):
            assert t["caring_message"]

    def test_points(self):
        for t in generate_daily_tasks("u1"):
            assert t["points"] > 0

    def test_deadline(self):
        for t in generate_daily_tasks("u1"):
            assert t["deadline"] is not None

    def test_trigger_source(self):
        for t in generate_daily_tasks("u1"):
            assert t["trigger_source"] == "cron"


class TestMealPhoto:
    def test_breakfast(self):
        t = generate_meal_photo_task("u1", "breakfast")
        assert "早餐" in t["title"] and t["category"] == "diet"

    def test_lunch(self):
        assert "午餐" in generate_meal_photo_task("u1", "lunch")["title"]

    def test_dinner(self):
        assert "晚餐" in generate_meal_photo_task("u1", "dinner")["title"]


class TestQuiz:
    def test_metadata(self):
        t = generate_daily_quiz("u1")
        assert t["category"] == "quiz"
        m = t["metadata"]
        assert all(k in m for k in ("quiz_options", "quiz_answer", "quiz_explanation"))

    def test_answer_in_options(self):
        m = generate_daily_quiz("u1")["metadata"]
        assert m["quiz_answer"] in m["quiz_options"]


class TestHbA1c:
    def test_reminder(self):
        t = generate_hba1c_reminder("u1")
        assert t["category"] == "checkup" and "HbA1c" in t["title"]


class TestQuizBank:
    def test_not_empty(self):
        assert len(QUIZ_BANK) >= 5

    def test_entries_valid(self):
        for q in QUIZ_BANK:
            assert q["answer"] in q["options"]
            assert q["explanation"]
