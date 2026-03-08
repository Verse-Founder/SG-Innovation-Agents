"""
scheduler/celery_app.py
Celery 应用实例 + Beat 调度表
"""
from celery import Celery
from celery.schedules import crontab
from config import settings

celery_app = Celery(
    "task_agent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Singapore",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "push-daily-tasks-7am": {
        "task": "scheduler.daily_routine.push_daily_tasks",
        "schedule": crontab(hour=7, minute=0),
    },
    "push-breakfast-photo-8am": {
        "task": "scheduler.daily_routine.push_meal_photo_reminder",
        "schedule": crontab(hour=8, minute=0),
        "kwargs": {"meal": "breakfast"},
    },
    "push-lunch-photo-12pm": {
        "task": "scheduler.daily_routine.push_meal_photo_reminder",
        "schedule": crontab(hour=12, minute=0),
        "kwargs": {"meal": "lunch"},
    },
    "push-dinner-photo-6pm": {
        "task": "scheduler.daily_routine.push_meal_photo_reminder",
        "schedule": crontab(hour=18, minute=0),
        "kwargs": {"meal": "dinner"},
    },
    "push-daily-quiz-8pm": {
        "task": "scheduler.daily_routine.push_daily_quiz",
        "schedule": crontab(hour=20, minute=0),
    },
    "push-steps-reminder-9pm": {
        "task": "scheduler.daily_routine.push_steps_reminder",
        "schedule": crontab(hour=21, minute=0),
    },
    "check-hba1c-quarterly": {
        "task": "scheduler.daily_routine.check_hba1c_reminder",
        "schedule": crontab(hour=9, minute=0, day_of_month="1"),
    },
}
