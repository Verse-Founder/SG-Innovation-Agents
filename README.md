# Dynamic Task Publication (DTP) Agent for Diabetes Management

This repository contains the **Dynamic Task Publication (DTP)** system, an AI-driven intervention engine designed to help diabetic patients manage their health through personalized exercise and routine task suggestions.

## 🚀 Overview

The DTP Agent leverages real-time health telemetry (CGM, Apple Watch) to deliver hyper-personalized "nundges". Unlike traditional step-trackers, the DTP Agent understands the user's metabolic state, current location, and clinical safety requirements.

### Key Features

- **Personalized Rule Engine**: Automatically adjusts exercise targets based on the user's BMI and real-time blood glucose levels.
- **Sea-Lion LLM Reasoning Pipeline**: 
  - **Analyst**: Processes telemetry and calculates caloric deficits.
  - **Advisor**: Interprets data to provide safe, clinical-grade exercise advice.
  - **Writer**: Generates warm, human-centric push notifications in multiple languages (EN, ZH, MS, etc.).
- **Safety Guards**: Includes a "Low BG Safeguard" that immediately suppresses exercise suggestions if the user is at risk of hypoglycemia.
- **Geo-Aware Recommendations**: Integrates with Google Maps to recommend 3 optimal parks within a 1km-2km radius for walking.
- **Routine Task Management**:
  - **Vision AI Meal Logging**: Verifies food photos using Gemini VLM.
  - **Daily Health Quizzes**: Encourages health literacy through gamified participation.
- **Gamification**: A "Flower & Points" engine that converts clinical data into visual rewards (blooming flowers).

## 🛠 Technology Stack

- **Backend**: FastAPI (Python 3.10+)
- **LLM**: Sea-Lion (aisingapore/Qwen-SEA-LION-v4-32B-IT) via LangGraph
- **Vision AI**: Gemini VLM
- **Database**: PostgreSQL (SQLAlchemy)
- **Geospatial**: Google Maps Places API
- **Dev Console**: Interactive HTML/JS dashboard for testing and simulation.

## 📦 Project Structure

```text
task_publish/
├── api/                # FastAPI routes (Dynamic Tasks, Routine Tasks)
├── config/             # Configuration & Environment loading
├── db/                 # Models, Migrations, and Session management
├── task_agent/         # Core AI Logic
│   ├── nodes/          # LangGraph Nodes (Analyst, Advisor, Writer)
│   ├── graph.py        # LangGraph Orchestration
│   ├── rule_engine.py  # Clinical decision logic
│   └── map_tool.py     # Google Maps integration
├── sea_lion_client.py  # Custom LLM API Client
├── seed_db.py          # Database seeding script for demo users
├── main.py             # Application entry point
└── demo_console.html   # Sandbox testing interface
```

## 🚦 Getting Started

### 1. Prerequisites
- Python 3.10+
- PostgreSQL
- API Keys: Sea-Lion, Google Maps, Gemini

### 2. Setup
```bash
# Clone the repository
git clone <repo-url>
cd task_publish

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file based on `.env.example`:
```env
SEA_LION_API_KEY="your_key"
GOOGLE_MAPS_API_KEY="your_key"
GEMINI_API_KEY="your_key"
DATABASE_URL="postgresql+psycopg2://user:password@localhost/task_publish"
```

### 4. Seed Database
```bash
python seed_db.py
```

### 5. Run Server
```bash
uvicorn main:app --reload
```
Open `demo_console.html` in your browser to start simulating users (Bob, Alice, Charlie).

## 📄 License
This project is part of the SG Innovation Initiative. See LICENSE for details.
