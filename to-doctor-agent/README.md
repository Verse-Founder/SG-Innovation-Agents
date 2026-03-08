# To-Doctor Agent — Patient Health Report System

English | [中文](README_CN.md)

AI-powered medical report generation agent that bridges patient health data to doctors. Built for the SG Innovation Challenge 2026.

This module is part of the **Diabetes Guardian** multi-agent platform, responsible for generating on-demand health reports, managing doctor-patient authorization, and providing appointment suggestions.

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

# 6. Start API server (port 8200)
make run
```

## Architecture

```
Data Sources              LangGraph Pipeline                    Outputs
------------              ------------------                    -------
Shared DB             ->  data_collector                     -> JSON Report
  (task-agent tables)     Aggregate patient health data          Structured data
                          |
Patient Profile       ->  trend_analysis                     -> PDF Report
  + Health Logs           Glucose, eGFR, medication, activity    Downloadable file
                          |
Behavior Patterns     ->  risk_summary (SEA-LION)            -> Appointments
  + Task Completions      AI Medical Advisor                     Smart scheduling
                          |
                         recommendation
                          Appointment + prescription advice
                          |
                         report_formatter
                          JSON + PDF generation
```

### Report Trigger Flow

```
Patient clicks "Generate Report"  ->  LangGraph Pipeline  ->  Report saved (JSON + PDF)
                                                           ->  Patient can view anytime

Doctor requests access  ->  Patient authorizes  ->  Doctor views report (with audit log)
```

## Project Structure

```
to-doctor-agent/
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
│   └── routes.py                   # /reports/*, /auth/*, /appointments/*, /prescriptions/*
│
├── config/
│   └── settings.py                 # Shared DB_URL, PDF config, medical constants
│
├── db/                             # Database layer (SQLAlchemy 2.0 async, shared DB)
│   ├── models.py                   # ORM models: MedicalReport, ReportAuthorization,
│   │                               #   Prescription, AppointmentSuggestion, AuditLog
│   ├── session.py                  # AsyncSession factory (shared DB_URL with task-agent)
│   └── crud.py                     # CRUD: reports, auth, prescriptions, appointments, audit
│
├── engine/                         # Core intelligence engines
│   ├── report_generator.py         # Report data aggregation + text summary
│   ├── trend_analyzer.py           # Glucose, eGFR, medication, activity trend analysis
│   ├── appointment_advisor.py      # Smart scheduling: nephrology, endocrinology, routine
│   ├── prescription_manager.py     # Prescription validation + mock HIS integration
│   └── data_masker.py              # PII masking: name, phone, address, ID number
│
├── graph/
│   └── builder.py                  # LangGraph: collect -> analyze -> summarize -> format
│
├── pdf/
│   └── generator.py                # ReportLab PDF generation (tables, charts, summaries)
│
├── schemas/                        # Pydantic v2 data models
│   ├── report.py                   # ReportGenerateRequest, ReportResponse
│   ├── authorization.py            # AuthRequest, AuthGrant, AuthResponse
│   └── prescription.py             # PrescriptionCreate, PrescriptionResponse
│
├── state/
│   └── report_state.py             # LangGraph shared state (TypedDict)
│
├── utils/
│   ├── llm_factory.py              # SEA-LION API wrapper
│   ├── time_utils.py               # SGT timezone utilities
│   ├── retry.py                    # Async retry decorator (exponential backoff)
│   ├── audit.py                    # Audit logging utility
│   └── mock_data.py                # Mock patient health data for testing
│
└── tests/                          # 70 tests, pytest + pytest-asyncio
    ├── conftest.py                 # Shared fixtures
    ├── test_trend_analyzer.py      # Trend analysis: glucose, eGFR, medication, activity
    ├── test_report_engine.py       # Report generation + summary
    ├── test_data_masker.py         # PII masking
    ├── test_appointment.py         # Appointment suggestion logic
    ├── test_prescription.py        # Prescription validation
    ├── test_db.py                  # Database CRUD (in-memory SQLite)
    └── test_api.py                 # FastAPI route tests
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/reports/generate` | Generate health report (idempotent via request_id) |
| `GET`  | `/api/v1/reports/{report_id}` | View report JSON (with access control) |
| `GET`  | `/api/v1/reports/{report_id}/pdf` | Download report PDF |
| `GET`  | `/api/v1/reports/user/{user_id}` | List all reports for a user |
| `POST` | `/api/v1/auth/request` | Doctor requests report access |
| `POST` | `/api/v1/auth/grant` | Patient grants/denies authorization |
| `GET`  | `/api/v1/auth/pending/{user_id}` | List pending authorization requests |
| `GET`  | `/api/v1/appointments/{user_id}` | Get appointment suggestions |
| `POST` | `/api/v1/prescriptions` | Record prescription (mock HIS) |
| `GET`  | `/api/v1/prescriptions/{user_id}` | View prescription history |
| `GET`  | `/api/v1/health` | Health check |

## Fault Tolerance

| Scenario | Handling |
|----------|----------|
| **Missing data** | Report marks incomplete sections, generates based on available data |
| **LLM timeout** | Falls back to rule-based summary generation |
| **Duplicate requests** | Idempotent via `request_id` — same ID returns existing report |
| **DB/LLM failure** | Auto-retry 3 times with exponential backoff |

## Security

| Feature | Implementation |
|---------|---------------|
| **Access control** | Doctors can only view patient-authorized reports; unauthorized = 403 |
| **Data masking** | Patient PII (name, phone, address) auto-masked in reports |
| **Audit logs** | All report generation, authorization, and access events are logged |
| **Sensitive storage** | Patient identifiers hashed for log storage |

## Output Example

```json
{
  "status": "ok",
  "data": {
    "report_id": "a1b2c3d4-...",
    "status": "completed",
    "summary": "Blood glucose: avg 7.2 mmol/L, well controlled. High episodes: 3, Low: 0.\nRenal function: eGFR 85 mL/min (CKD G1). No declining trend.\nMedication adherence: 88% (good).\nActivity: avg 6200 steps/day.",
    "data_completeness": {
      "glucose": true,
      "egfr": true,
      "medication": true,
      "activity": true,
      "tasks": true
    },
    "appointment_count": 2,
    "pdf_available": true
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SEALION_API_KEY` | — | SEA-LION API key |
| `SEALION_BASE_URL` | `https://api.sea-lion.ai/v1` | SEA-LION endpoint |
| `DB_URL` | `sqlite+aiosqlite:///./task_agent.db` | Shared database URL |
| `PDF_OUTPUT_DIR` | `./generated_reports` | PDF output directory |
| `ENV` | `development` | Environment mode |
| `LOG_LEVEL` | `INFO` | Logging level |

## Tech Stack

- **Framework**: LangGraph (state graph) + FastAPI
- **Language**: Python 3.11+
- **LLM**: SEA-LION (Reasoning 70B + Instruct 8B)
- **Database**: MySQL 8.0 / SQLite (dev) via SQLAlchemy 2.0 async (shared with task-agent)
- **PDF**: ReportLab
- **Validation**: Pydantic v2
- **Testing**: pytest + pytest-asyncio (70 tests)

## Testing

```bash
make test      # Mock mode (70 tests, <1s)
make test-live # Real API mode (requires .env config)
make coverage  # Tests + coverage report
```

## Team Collaboration

| Team Member | Repo | Integration |
|-------------|------|-------------|
| baileybei | [Health-Companion](https://github.com/baileybei/Health-Companion) (Chatbot) | Chat insights feed into reports |
| juliawangjiayu | [Diabetes_Guardian](https://github.com/juliawangjiayu/Diabetes_Guardian) (Alert Agent) | Alert data included in risk assessment |
| Jamieee0531 | [SG-INNOVATION](https://github.com/Jamieee0531/SG-INNOVATION) (Vision Agent) | Food analysis data in reports |
| Verse-Founder | [task-agent](../task-agent/) (Task Agent) | Shared DB, prescription triggers |
