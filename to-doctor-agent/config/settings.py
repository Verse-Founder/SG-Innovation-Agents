"""
config/settings.py
全局配置：共享 task-agent 数据库 + PDF/API 设置
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

# ── 数据库（共享 task-agent） ────────────────────────────
DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///./task_agent.db")

# ── PDF 配置 ─────────────────────────────────────────────
PDF_OUTPUT_DIR = os.getenv("PDF_OUTPUT_DIR", "./generated_reports")
PDF_FONT_NAME = "Helvetica"

# ── 报告配置 ─────────────────────────────────────────────
REPORT_DATA_DAYS = 30          # 报告默认覆盖天数
REPORT_GENERATION_TIMEOUT = 60  # LLM 生成超时秒数
MAX_RETRY_ATTEMPTS = 3          # 重试次数

# ── 医学参考值 ───────────────────────────────────────────
GLUCOSE_FASTING_NORMAL = (3.9, 6.1)    # mmol/L
GLUCOSE_POSTPRANDIAL_NORMAL = (3.9, 7.8)
EGFR_NORMAL_MIN = 90.0                  # mL/min/1.73m²
EGFR_STAGE_THRESHOLDS = {
    "G1": 90, "G2": 60, "G3a": 45, "G3b": 30, "G4": 15, "G5": 0,
}
HBA1C_TARGET = 7.0  # %

# ── 任务配置 ─────────────────────────────────────────────
DEFAULT_DAILY_STEPS_GOAL = 6000
