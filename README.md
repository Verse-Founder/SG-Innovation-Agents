# 🤖 Task Agent — Personalized Diabetes Health Task Management System

> SG Innovation Challenge 2026 · Track 1 · Verse-Founder

[中文版 README 请点这里 / Chinese Version](#-任务发布agent--糖尿病个性化健康任务管理系统)

---

## Overview

Task Agent is a core module of the Diabetes Guardian platform. It generates personalized health management tasks for diabetes patients using AI-driven medical analysis.

**Core Capabilities:**
- 🧠 **AI Medical Advisor**: SEA-LION reasoning model analyzes patient data and dynamically generates personalized tasks
- 🫘 **Renal Function Monitoring**: eGFR trend tracking, proteinuria / foam urine detection
- 📊 **Smart Checkup Scheduling**: Regular cycles + auto-advance visits when patient data deteriorates
- 💬 **Warm & Caring Tone**: All task descriptions use friendly, encouraging language (not clinical commands)
- 🎯 **Gamification Points**: Task completion points, streak multipliers, "energy stealing" (reserved)
- 🔗 **Upstream/Downstream Integration**: Receives triggers from chatbot / Alert Agent / doctor portal

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + Python 3.11+ |
| Agent | LangGraph (StateGraph) |
| LLM | SEA-LION (Reasoning + Instruct dual models) + Cloudflare fallback |
| Database | MySQL 8.0 (SQLAlchemy 2.0 async) / SQLite (dev) |
| Task Queue | Celery + Redis |
| Testing | pytest (41 tests) |

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
──────────────          ──────────────────                    ───────
⏰ Cron Scheduler   →  intake                              → MySQL Persistence
💬 Chatbot trigger  →  context_enrichment (+ chat history)  → 📱 Frontend Push
🚨 Alert Agent      →  risk_assessment (AI Medical Advisor) → 🎯 Points System
👨‍⚕️ Doctor Portal   →  task_generation (warm tone)
                     →  priority_ranking
                     →  output_formatter
```

## Project Structure

```
task-agent/
├── api/            # FastAPI routes
├── config/         # Settings + medical constants
├── engine/         # Core engines (AI analysis · renal · checkup · points)
├── graph/          # LangGraph graph definition
├── nodes/          # LangGraph nodes (6 nodes)
├── schemas/        # Pydantic v2 data models
├── state/          # LangGraph shared state
├── utils/          # Utilities (LLM · timezone · mock data)
├── tests/          # Tests (41 test cases)
├── main.py         # CLI entry point
└── Makefile        # Shortcut commands
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/trigger/chatbot` | Receive chatbot's task_trigger |
| POST | `/api/v1/trigger/alert` | Receive Alert Agent signal |
| POST | `/api/v1/trigger/doctor` | Receive doctor-assigned tasks (reserved) |
| GET  | `/api/v1/tasks/{user_id}` | Query user's current tasks |
| POST | `/api/v1/tasks/complete` | Mark task complete, calculate points |
| GET  | `/api/v1/points/{user_id}` | Query points balance |

## Testing

```bash
make test      # Mock mode (41 tests, 0.27s)
make test-live # Real API mode (requires .env config)
make coverage  # Coverage report
```

## Team Collaboration

| Team Member | Repo | Integration |
|-------------|------|-------------|
| Bailey ([Health-Companion](https://github.com/baileybei/Health-Companion)) | Chatbot | Triggers via `POST /api/v1/trigger/chatbot` |
| Julia ([Diabetes_Guardian](https://github.com/juliawangjiayu/Diabetes_Guardian)) | Alert Agent | Triggers via `POST /api/v1/trigger/alert` |
| Jamie ([SG-INNOVATION](https://github.com/Jamieee0531/SG-INNOVATION)) | Vision Agent | Food analysis results feed into `chat_insights` |

---

# 🤖 任务发布Agent — 糖尿病个性化健康任务管理系统

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
| 测试 | pytest（41 个测试用例） |

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
├── api/            # FastAPI 路由
├── config/         # 配置 + 医学常量
├── engine/         # 核心引擎（AI分析 · 肾功能 · 复诊 · 积分）
├── graph/          # LangGraph 图定义
├── nodes/          # LangGraph 节点（6 个）
├── schemas/        # Pydantic v2 数据模型
├── state/          # LangGraph 共享状态
├── utils/          # 工具（LLM · 时区 · Mock数据）
├── tests/          # 测试（41 个测试用例）
├── main.py         # CLI 入口
└── Makefile        # 快捷命令
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/trigger/chatbot` | 接收 chatbot 的 task_trigger |
| POST | `/api/v1/trigger/alert` | 接收预警 Agent 信号 |
| POST | `/api/v1/trigger/doctor` | 接收医生端任务（预留） |
| GET  | `/api/v1/tasks/{user_id}` | 查询用户当前任务 |
| POST | `/api/v1/tasks/complete` | 标记任务完成，计算积分 |
| GET  | `/api/v1/points/{user_id}` | 查询积分余额 |

## 测试

```bash
make test      # Mock 模式（41 tests, 0.27s）
make test-live # 真实 API（需配置 .env）
make coverage  # 覆盖率报告
```

## 团队协作

| 成员 | 仓库 | 集成方式 |
|------|------|---------|
| Bailey ([Health-Companion](https://github.com/baileybei/Health-Companion)) | Chatbot | 通过 `POST /api/v1/trigger/chatbot` 触发 |
| Julia ([Diabetes_Guardian](https://github.com/juliawangjiayu/Diabetes_Guardian)) | 预警 Agent | 通过 `POST /api/v1/trigger/alert` 触发 |
| Jamie ([SG-INNOVATION](https://github.com/Jamieee0531/SG-INNOVATION)) | Vision Agent | 食物分析结果作为 `chat_insights` 输入 |
