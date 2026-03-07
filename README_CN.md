# 任务发布Agent — 糖尿病个性化健康任务管理系统

[English](README.md) | 中文

> SG Innovation Challenge 2026 · Track 1 · Verse-Founder

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

## 架构

```
触发源                    LangGraph 流水线                      输出
------                  ----------------                    ----
⏰ 定时调度器           →  intake（信号接收）                  → MySQL 持久化
💬 Chatbot 触发         →  context_enrichment（上下文丰富）    → 📱 前端推送
🚨 预警 Agent           →  risk_assessment（AI 医学分析）      → 🎯 积分系统
👨‍⚕️ 医生端             →  task_generation（温暖话术生成）
                        →  priority_ranking（排序去重）
                        →  output_formatter（格式化输出）
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
| Bailey ([Health-Companion](https://github.com/baileybei/Health-Companion)) | Chatbot | 通过 `POST /api/v1/trigger/chatbot` 触发 |
| Julia ([Diabetes_Guardian](https://github.com/juliawangjiayu/Diabetes_Guardian)) | 预警 Agent | 通过 `POST /api/v1/trigger/alert` 触发 |
| Jamie ([SG-INNOVATION](https://github.com/Jamieee0531/SG-INNOVATION)) | Vision Agent | 食物分析结果作为 `chat_insights` 输入 |
