# Task Agent — Personalized Diabetes Health Task Management

English | [中文](README_CN.md)

AI-powered personalized health task generation agent for diabetic patients in Singapore. Built for the SG Innovation Challenge 2026.

This module is part of the **Diabetes Guardian** multi-agent platform, responsible for generating, scheduling, and managing health tasks through AI medical analysis.

## Quick Start

```bash
# 1. Create virtual environment
python3 -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env and add your SEA-LION API KEY

# 4. Run tests
make test

# 5. Launch CLI Demo
python main.py

# 6. Start API server (port 8100)
make run
```

## Architecture

```
Trigger Sources          LangGraph Pipeline                    Outputs
--------------          ------------------                    -------
Cron Scheduler       ->  intake                              -> MySQL Persistence
Chatbot trigger      ->  context_enrichment (+ chat history)  -> Frontend Push
Alert Agent          ->  risk_assessment (AI Medical Advisor) -> Points System
Doctor Portal        ->  task_generation (warm tone)
                     ->  priority_ranking
                     ->  output_formatter
```

### LangGraph Pipeline

```
START -> intake -> context_enrichment -> risk_assessment
      -> task_generation -> priority_ranking -> output_formatter -> END
```

## Project Structure

```
task-agent/
├── README.md
├── README_CN.md
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
│   ├── intelligence.py             # TaskIntelligenceEngine (SEA-LION reasoning)
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
        "title": "Daily Step Check-in",
        "category": "exercise",
        "description": "Goal: 6000 steps. Light to moderate walking is great!",
        "caring_message": "Every step counts! Today's goal is 6000 steps, you can do it!",
        "points": 10,
        "priority": "medium"
      },
      {
        "title": "Blood Glucose Monitoring",
        "category": "monitoring",
        "description": "Please record your blood glucose level (fasting or postprandial).",
        "caring_message": "Remember to check your blood glucose. Understanding your body helps you take better care of yourself.",
        "points": 5,
        "priority": "medium"
      }
    ],
    "risk_assessment": {
      "overall_risk": "medium",
      "concerns": ["renal_function_declining", "dawn_phenomenon_detected"]
    },
    "notifications": [
      "Time to take your medication! Staying on schedule keeps your body in good shape."
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

## Testing

```bash
make test      # Mock mode (73 tests, <1s)
make test-live # Real API mode (requires .env config)
make coverage  # Tests + coverage report
```

## Team Collaboration

| Team Member | Repo | Integration |
|-------------|------|-------------|
| baileybei | [Health-Companion](https://github.com/baileybei/Health-Companion) (Chatbot) | Triggers via `POST /api/v1/trigger/chatbot`|
| juliawangjiayu | [Diabetes_Guardian](https://github.com/juliawangjiayu/Diabetes_Guardian) (Alert Agent) | Triggers via `POST /api/v1/trigger/alert`|
| Jamieee0531 | [SG-INNOVATION](https://github.com/Jamieee0531/SG-INNOVATION) (Vision Agent) | Food analysis results feed into `chat_insights`|

