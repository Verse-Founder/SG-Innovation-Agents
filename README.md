# Task Agent — Personalized Diabetes Health Task Management

English | [中文](#任务发布agent--糖尿病个性化健康任务管理系统)

AI-powered personalized health task generation agent for diabetic patients in Singapore. Built for the SG Innovation Challenge 2026.

This module is part of the **Diabetes Guardian** multi-agent platform, responsible for generating, scheduling, and managing health tasks through AI medical analysis.

## Architecture

```
Trigger Sources              LangGraph Pipeline                       Outputs
──────────────              ──────────────────                       ───────
⏰ Cron Scheduler        →  intake                                 → MySQL / SQLite
   (Celery Beat)             Receive & normalize trigger signals       Persistence
                             |
💬 Chatbot trigger       →  context_enrichment                     → 📱 Frontend Push
   (Bailey)                  Patient profile + health records          Task notifications
                             + behavior patterns + chat history
                             |
🚨 Alert Agent           →  risk_assessment                        → 🎯 Points System
   (Julia)                   AI Medical Advisor (SEA-LION)             Gamification engine
                             + renal monitor + checkup scheduler
                             |
👨‍⚕️ Doctor Portal        →  task_generation
   (reserved)                Warm & caring tone descriptions
                             |
                            priority_ranking
                             Deduplicate & sort by urgency
                             |
                            output_formatter
                             Structured JSON payload
```

### LangGraph Pipeline

```
START → intake → context_enrichment → risk_assessment
      → task_generation → priority_ranking → output_formatter → END
```

## Quick Start

### 1. Install

```bash
git clone <repo-url>
cd task-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys:
# SEALION_API_KEY=your_key
# SEALION_BASE_URL=https://api.sea-lion.ai/v1
# DB_URL=sqlite+aiosqlite:///./task_agent.db
```

### 3. Run

```bash
# CLI Demo (interactive task generation)
python main.py

# Start API server (port 8100)
make run

# Start Celery Beat scheduler (requires Redis)
make celery-beat
```

### 4. Test

```bash
make test      # Run all tests (73 tests, <1s)
make test-live # Real API mode (requires .env config)
make coverage  # Tests + coverage report
```

## Project Structure

```
task-agent/
├── README.md
├── Makefile
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gitignore
├── main.py                         # CLI entry point
│
├── api/                            # FastAPI interface layer
│   ├── app.py                      # FastAPI app + lifespan (auto DB init)
│   └── routes.py                   # /trigger/*, /tasks/*, /points/*
│
├── config/
│   └── settings.py                 # pydantic-settings: API keys, DB URL, medical constants
│
├── db/                             # Database layer (SQLAlchemy 2.0 async)
│   ├── models.py                   # ORM models: Task, UserHealthLog, TaskCompletion,
│   │                               #   PointsLedger, BehaviorPattern, ChatInsight
│   ├── session.py                  # AsyncSession factory + connection pool
│   └── crud.py                     # CRUD operations for all models
│
├── scheduler/                      # Celery Beat scheduled tasks (non-Agent)
│   ├── celery_app.py               # Celery config + Beat schedule (SGT timezone)
│   └── daily_routine.py            # Daily pushes: steps, meals, quiz, medication,
│                                   #   glucose monitoring, HbA1c reminder
│
├── engine/                         # Core intelligence engines
│   ├── intelligence.py             # 🧠 TaskIntelligenceEngine (SEA-LION reasoning)
│   ├── renal_monitor.py            # Renal function: eGFR trend, proteinuria, foam urine
│   ├── checkup_scheduler.py        # Smart checkup: regular + dynamic early visits
│   └── points_engine.py            # Gamification: points, streaks, multipliers
│
├── graph/
│   └── builder.py                  # LangGraph StateGraph definition
│
├── nodes/                          # LangGraph processing nodes
│   ├── intake.py                   # Trigger signal normalization
│   ├── context_enrichment.py       # Patient data aggregation + chat history
│   ├── risk_assessment.py          # AI medical analysis + renal + checkup
│   ├── task_generation.py          # Task creation with warm caring messages
│   ├── priority_ranking.py         # Priority sort + deduplication
│   └── output_formatter.py         # Structured JSON + push notifications
│
├── schemas/                        # Pydantic v2 data models
│   ├── task.py                     # TaskCreate, TaskResponse, TaskBatch
│   ├── health.py                   # HealthSnapshot, RenalIndicators, GlucosePattern
│   └── points.py                   # PointsTransaction, PointsBalance
│
├── state/
│   └── task_state.py               # LangGraph shared state (TypedDict)
│
├── utils/
│   ├── llm_factory.py              # SEA-LION API: reasoning + instruct dual models
│   ├── time_utils.py               # SGT timezone, week slicing
│   └── mock_data.py                # Mock CGM glucose, eGFR, chat summaries
│
└── tests/                          # 73 tests, pytest + pytest-asyncio
    ├── conftest.py                 # Shared fixtures (mock LLM)
    ├── test_graph.py               # End-to-end graph pipeline tests
    ├── test_intelligence.py        # AI engine + rule-based fallback
    ├── test_renal_monitor.py       # Renal function analysis
    ├── test_checkup_scheduler.py   # Smart checkup scheduling
    ├── test_points_engine.py       # Points calculation + streaks
    ├── test_db.py                  # Database CRUD (in-memory SQLite)
    ├── test_api.py                 # FastAPI route tests
    └── test_scheduler.py           # Scheduled task logic
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/trigger/chatbot` | Receive chatbot task trigger |
| `POST` | `/api/v1/trigger/alert` | Receive Alert Agent signal |
| `POST` | `/api/v1/trigger/doctor` | Receive doctor-assigned tasks (reserved) |
| `GET`  | `/api/v1/tasks/{user_id}` | Query user's current tasks |
| `POST` | `/api/v1/tasks/complete` | Mark task complete, award points |
| `POST` | `/api/v1/tasks/batch` | Batch create tasks |
| `GET`  | `/api/v1/points/{user_id}` | Query points balance |
| `GET`  | `/health` | Health check |

## Output Example

```json
{
  "status": "ok",
  "data": {
    "user_id": "patient_001",
    "tasks": [
      {
        "title": "今日步数打卡",
        "category": "exercise",
        "description": "目标：6000 步。轻到中等强度的步行就很好！",
        "caring_message": "每一步都算数！今天的目标是 6000 步，你能行的 💪",
        "points": 10,
        "priority": "medium"
      },
      {
        "title": "血糖监测",
        "category": "monitoring",
        "description": "请记录您的血糖数值（空腹或餐后均可）。",
        "caring_message": "记得测一下血糖哦 🩸 了解自己的身体状态，才能更好地照顾自己～",
        "points": 5,
        "priority": "medium"
      }
    ],
    "risk_assessment": {
      "overall_risk": "medium",
      "concerns": ["renal_function_declining", "dawn_phenomenon_detected"]
    },
    "notifications": [
      "💊 该吃药了哦，按时服药，才能让身体稳稳当当的！"
    ]
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SEALION_API_KEY` | — | SEA-LION API key |
| `SEALION_BASE_URL` | `https://api.sea-lion.ai/v1` | SEA-LION endpoint |
| `DB_URL` | `sqlite+aiosqlite:///./task_agent.db` | Database URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for Celery |
| `ENV` | `development` | Environment mode |
| `LOG_LEVEL` | `INFO` | Logging level |

## Tech Stack

- **Framework**: LangGraph (state graph orchestration) + FastAPI
- **Language**: Python 3.11+
- **LLM**: SEA-LION (Reasoning 70B + Instruct 8B dual models)
- **Database**: MySQL 8.0 / SQLite (dev) via SQLAlchemy 2.0 async
- **Task Queue**: Celery + Redis (Beat scheduler)
- **Validation**: Pydantic v2
- **HTTP**: httpx + requests
- **Testing**: pytest + pytest-asyncio (73 tests)

## Team Collaboration

| Team Member | Repo | Integration |
|-------------|------|-------------|
| Bailey ([Health-Companion](https://github.com/baileybei/Health-Companion)) | Chatbot | Triggers via `POST /trigger/chatbot` |
| Julia ([Diabetes_Guardian](https://github.com/juliawangjiayu/Diabetes_Guardian)) | Alert Agent | Triggers via `POST /trigger/alert` |
| Jamie ([SG-INNOVATION](https://github.com/Jamieee0531/SG-INNOVATION)) | Vision Agent | Food analysis → `chat_insights` |

## License

MIT — SG Innovation Challenge 2026

---

# 任务发布Agent — 糖尿病个性化健康任务管理系统

> SG Innovation Challenge 2026 · Track 1 · Verse-Founder

## 概述

Task Agent 是糖尿病管理平台的核心模块之一，负责为患者生成个性化的健康管理任务。

**核心能力：**
- 🧠 **AI 医学顾问**：使用 SEA-LION 推理模型分析患者数据，动态生成个性化任务
- 🫘 **肾功能监测**：eGFR 趋势跟踪、蛋白尿、泡沫尿检测
- 📊 **智能复诊调度**：常规周期 + 数据异常自动提前复诊建议
- 💬 **温暖话术**：所有任务描述体现人文关怀，像朋友一样说话
- 🎯 **积分激励**：任务完成积分、连续完成乘数、"偷能量"预留
- 🔗 **上下游集成**：接收 chatbot / 预警Agent / 医生端的触发信号

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | FastAPI + Python 3.11+ |
| Agent | LangGraph (StateGraph) |
| LLM | SEA-LION（推理 + 对话双模型）+ Cloudflare 备用 |
| 数据库 | MySQL 8.0 (SQLAlchemy 2.0 async) / SQLite（开发） |
| 任务队列 | Celery + Redis |
| 测试 | pytest（73 个测试用例） |

## 快速开始

```bash
# 1. 创建虚拟环境
python3 -m venv .venv && source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 SEA-LION API KEY

# 4. 运行测试
make test

# 5. 启动 CLI Demo
python main.py

# 6. 启动 API 服务（端口 8100）
make run
```

## 项目结构

```
task-agent/
├── api/                            # FastAPI 路由
│   ├── app.py                      # FastAPI 应用 + lifespan（自动建表）
│   └── routes.py                   # /trigger/*, /tasks/*, /points/*
│
├── config/
│   └── settings.py                 # pydantic-settings 配置 + 医学常量
│
├── db/                             # 数据库层（SQLAlchemy 2.0 async）
│   ├── models.py                   # ORM 模型：Task, UserHealthLog,
│   │                               #   TaskCompletion, PointsLedger 等 6 张表
│   ├── session.py                  # AsyncSession 工厂 + 连接池
│   └── crud.py                     # 数据库 CRUD 操作封装
│
├── scheduler/                      # 定时任务（Celery Beat，非 Agent）
│   ├── celery_app.py               # Celery 配置 + Beat 调度表（新加坡时区）
│   └── daily_routine.py            # 每日推送：步数、三餐、用药、血糖、每日一题
│
├── engine/                         # 核心智能引擎
│   ├── intelligence.py             # 🧠 统一智能引擎（SEA-LION 推理模型）
│   ├── renal_monitor.py            # 肾功能监测：eGFR · 蛋白尿 · 泡沫尿
│   ├── checkup_scheduler.py        # 智能复诊：常规周期 + 动态提前
│   └── points_engine.py            # 积分系统：打卡 · 连续 · 乘数
│
├── graph/
│   └── builder.py                  # LangGraph 图定义
│
├── nodes/                          # LangGraph 节点
│   ├── intake.py                   # 触发信号标准化
│   ├── context_enrichment.py       # 患者数据聚合 + 聊天记录分析
│   ├── risk_assessment.py          # AI 医学分析 + 肾功能 + 复诊
│   ├── task_generation.py          # 任务生成 + 温暖关怀话术
│   ├── priority_ranking.py         # 优先级排序 + 去重
│   └── output_formatter.py         # 结构化 JSON + 推送通知
│
├── schemas/                        # Pydantic v2 数据模型
│   ├── task.py                     # TaskCreate, TaskResponse
│   ├── health.py                   # HealthSnapshot, RenalIndicators
│   └── points.py                   # PointsTransaction, PointsBalance
│
├── state/
│   └── task_state.py               # LangGraph 共享状态（TypedDict）
│
├── utils/
│   ├── llm_factory.py              # SEA-LION API 封装（推理 + 对话双模型）
│   ├── time_utils.py               # 新加坡时区、周切片
│   └── mock_data.py                # Mock 数据（CGM 血糖、eGFR、聊天摘要）
│
└── tests/                          # 73 个测试用例
    ├── conftest.py                 # 共享 fixtures
    ├── test_graph.py               # 端到端图流水线测试
    ├── test_intelligence.py        # AI 引擎 + 规则型回退
    ├── test_renal_monitor.py       # 肾功能分析
    ├── test_checkup_scheduler.py   # 智能复诊调度
    ├── test_points_engine.py       # 积分计算 + 连续完成
    ├── test_db.py                  # 数据库 CRUD（in-memory SQLite）
    ├── test_api.py                 # FastAPI 路由测试
    └── test_scheduler.py           # 定时任务逻辑
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/trigger/chatbot` | 接收 chatbot 的 task_trigger |
| `POST` | `/api/v1/trigger/alert` | 接收预警 Agent 信号 |
| `POST` | `/api/v1/trigger/doctor` | 接收医生端任务（预留） |
| `GET`  | `/api/v1/tasks/{user_id}` | 查询用户当前任务 |
| `POST` | `/api/v1/tasks/complete` | 标记任务完成，计算积分 |
| `POST` | `/api/v1/tasks/batch` | 批量创建任务 |
| `GET`  | `/api/v1/points/{user_id}` | 查询积分余额 |
| `GET`  | `/health` | 健康检查 |

## 测试

```bash
make test      # Mock 模式（73 tests, <1s）
make test-live # 真实 API（需配置 .env）
make coverage  # 覆盖率报告
```

## 团队协作

| 成员 | 仓库 | 集成方式 |
|------|------|---------|
| Bailey ([Health-Companion](https://github.com/baileybei/Health-Companion)) | Chatbot | 通过 `POST /trigger/chatbot` 触发 |
| Julia ([Diabetes_Guardian](https://github.com/juliawangjiayu/Diabetes_Guardian)) | 预警 Agent | 通过 `POST /trigger/alert` 触发 |
| Jamie ([SG-INNOVATION](https://github.com/Jamieee0531/SG-INNOVATION)) | Vision Agent | 食物分析结果 → `chat_insights` |
