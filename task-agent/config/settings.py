"""
config/settings.py
全局配置：API、数据库、医学常量
使用 pydantic-settings（对标 Julia 的 diabetes-guardian）
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── 环境 ─────────────────────────────────────────────────
ENV = os.getenv("ENV", "development")
IS_DEV = ENV == "development"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── SEA-LION LLM ─────────────────────────────────────────
SEALION_API_KEY = os.getenv("SEALION_API_KEY", "")
SEALION_BASE_URL = os.getenv("SEALION_BASE_URL", "https://api.sea-lion.ai/v1")
SEALION_INSTRUCT_MODEL = "aisingapore/Qwen-SEA-LION-v4-32B-IT"
SEALION_REASONING_MODEL = "aisingapore/Llama-SEA-LION-v3.5-70B-R"

# Cloudflare 备用
CF_BASE_URL = "https://cf-sealion.e1521205.workers.dev"

# ── 数据库 ───────────────────────────────────────────────
DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///./task_agent.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ── 任务配置 ─────────────────────────────────────────────
DEFAULT_DAILY_CALORIES_GOAL = 300  # kcal
MEAL_PHOTO_TIMES = {"breakfast": "08:00", "lunch": "12:00", "dinner": "18:00"}
MEDICATION_REMINDER_ADVANCE_MIN = 15  # 提前N分钟提醒

# ── 积分配置 ─────────────────────────────────────────────
POINTS_DAILY_EXERCISE = 10
POINTS_MEAL_PHOTO = 5
POINTS_DAILY_QUIZ = 5
POINTS_MEDICATION_ON_TIME = 10
POINTS_WEEKLY_BONUS = 20
POINTS_STREAK_MULTIPLIER = 1.5  # 连续完成乘数

# ── 医学常量（糖尿病管理） ───────────────────────────────
# 血糖安全范围 (mmol/L)
GLUCOSE_LOW_THRESHOLD = 3.9        # 低血糖
GLUCOSE_CRITICAL_LOW = 3.0         # 严重低血糖
GLUCOSE_HIGH_THRESHOLD = 10.0      # 高血糖
GLUCOSE_CRITICAL_HIGH = 16.7       # 严重高血糖（禁止运动）
GLUCOSE_FASTING_HIGH = 7.0         # 空腹偏高
GLUCOSE_PRE_EXERCISE_MIN = 4.4     # 运动前最低血糖
GLUCOSE_PRE_EXERCISE_SNACK = 5.6   # 低于此值运动前需补餐

# HbA1c 目标
HBA1C_TARGET = 7.0                 # %
HBA1C_GOOD = 6.5                   # % 控制良好
HBA1C_TEST_INTERVAL_DAYS = 90      # 每3个月

# 肾功能 (eGFR: mL/min/1.73m²)
EGFR_NORMAL = 90
EGFR_MILD_DECLINE = 60             # 轻度下降
EGFR_MODERATE_DECLINE = 45         # 中度下降
EGFR_SEVERE_DECLINE = 30           # 重度下降
EGFR_KIDNEY_FAILURE = 15           # 肾衰竭
EGFR_DECLINE_ALERT_THRESHOLD = 5   # 3个月内下降>5需警觉

# 运动处方
EXERCISE_WEEKLY_AEROBIC_MIN = 150  # 每周有氧分钟
EXERCISE_BP_CONTRAINDICATION = 160  # 收缩压 > 160 禁运动
HEART_RATE_MAX_FORMULA = 220       # 最大心率 = 220 - 年龄

# 复诊周期
CHECKUP_HBA1C_MONTHS = 3
CHECKUP_FULL_BODY_MONTHS = 6
CHECKUP_EYE_MONTHS = 12
CHECKUP_RENAL_MONTHS = 6

# ── 意图/类别常量 ────────────────────────────────────────
TASK_TYPES = ["daily_routine", "weekly_personalized", "dynamic_risk", "doctor_assigned"]
TASK_CATEGORIES = ["exercise", "diet", "medication", "monitoring", "quiz", "checkup", "renal"]
TASK_PRIORITIES = ["critical", "high", "medium", "low"]

TRIGGER_SOURCES = ["cron", "chatbot", "alert_agent", "doctor", "system"]
