# To医生端Agent — 患者健康报告生成系统

[English](README.md) | 中文

To-Doctor Agent 是糖尿病管理平台的核心模块之一，负责将患者健康数据聚合为结构化医疗报告，桥接患者与医生之间的信息闭环。

**核心能力：**
- 📊 **按需报告生成**：患者主动点击生成，或医生请求+患者授权
- 🧠 **AI 风险评估**：SEA-LION 推理模型分析趋势，生成自然语言摘要
- 📄 **PDF 报告**：专业医疗报告格式，支持下载和打印
- 🔐 **权限控制**：医生仅能查看患者授权的报告，越权直接拦截
- 📅 **智能预约建议**：基于数据异常自动推荐科室和就诊时间
- 💊 **处方管理**：mock HIS 对接，处方自动转发至 task-agent 生成用药提醒
- 🛡️ **数据脱敏**：患者敏感信息自动脱敏，审计日志全程追踪

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | FastAPI + Python 3.11+ |
| Agent | LangGraph (StateGraph) |
| LLM | SEA-LION（推理模型） |
| 数据库 | 共享 task-agent 数据库（SQLAlchemy 2.0 async） |
| PDF | ReportLab |
| 测试 | pytest（70 个测试用例） |

## 快速开始

```bash
# 1. 创建虚拟环境
python3 -m venv .venv && source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env

# 4. 运行测试
make test

# 5. 启动 CLI Demo
python main.py

# 6. 启动 API 服务（端口 8200）
make run
```

## 项目结构

```
to-doctor-agent/
├── api/                            # FastAPI 路由
│   ├── app.py                      # 应用 + lifespan（自动建表）
│   └── routes.py                   # /reports/*, /auth/*, /appointments/*, /prescriptions/*
│
├── config/
│   └── settings.py                 # 共享数据库 URL + PDF 配置 + 医学常量
│
├── db/                             # 数据库层（共享 task-agent 数据库）
│   ├── models.py                   # 5 张新表：MedicalReport, ReportAuthorization,
│   │                               #   Prescription, AppointmentSuggestion, AuditLog
│   ├── session.py                  # AsyncSession 工厂
│   └── crud.py                     # CRUD 操作
│
├── engine/                         # 核心引擎
│   ├── report_generator.py         # 报告数据聚合 + 文字摘要
│   ├── trend_analyzer.py           # 血糖/eGFR/用药/运动趋势分析
│   ├── appointment_advisor.py      # 智能预约建议
│   ├── prescription_manager.py     # 处方管理 + mock HIS
│   └── data_masker.py              # 数据脱敏
│
├── graph/
│   └── builder.py                  # LangGraph 流水线（5 节点）
│
├── pdf/
│   └── generator.py                # ReportLab PDF 生成
│
├── schemas/                        # Pydantic v2 数据模型
├── state/                          # LangGraph 共享状态
├── utils/                          # 工具：LLM、重试、审计、Mock 数据
│
└── tests/                          # 70 个测试用例
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/reports/generate` | 生成健康报告（幂等） |
| `GET`  | `/api/v1/reports/{report_id}` | 查看报告 JSON（权限控制） |
| `GET`  | `/api/v1/reports/{report_id}/pdf` | 下载报告 PDF |
| `GET`  | `/api/v1/reports/user/{user_id}` | 查看所有报告 |
| `POST` | `/api/v1/auth/request` | 医生请求授权 |
| `POST` | `/api/v1/auth/grant` | 患者授予/拒绝授权 |
| `GET`  | `/api/v1/auth/pending/{user_id}` | 查看待处理授权 |
| `GET`  | `/api/v1/appointments/{user_id}` | 获取预约建议 |
| `POST` | `/api/v1/prescriptions` | 记录处方（mock HIS） |
| `GET`  | `/api/v1/prescriptions/{user_id}` | 查看处方历史 |

## 容错 & 安全

| 容错机制 | 说明 |
|---------|------|
| 数据缺失 | 标记不完整章节，基于已有数据生成 |
| LLM 超时 | 回退到规则型摘要 |
| 幂等请求 | 相同 request_id 返回已有报告 |
| 自动重试 | 3 次指数退避 |

| 安全特性 | 说明 |
|---------|------|
| 权限控制 | 越权访问返回 403 |
| 数据脱敏 | 姓名/手机/地址自动脱敏 |
| 审计日志 | 全部敏感操作可追溯 |

## 测试

```bash
make test      # Mock 模式（70 tests, <1s）
make test-live # 真实 API（需配置 .env）
make coverage  # 覆盖率报告
```

## 团队协作

| 成员 | 仓库 | 集成方式 |
|------|------|---------|
| baileybei | [Health-Companion](https://github.com/baileybei/Health-Companion) （Chatbot） | 聊天洞察纳入报告 |
| juliawangjiayu | [Diabetes_Guardian](https://github.com/juliawangjiayu/Diabetes_Guardian) （预警 Agent） | 预警数据纳入风险评估 |
| Jamieee0531 | [SG-INNOVATION](https://github.com/Jamieee0531/SG-INNOVATION) （Vision Agent） | 食物分析数据纳入报告 |
| Verse-Founder | [task-agent](../task-agent/) （任务发布 Agent） | 共享数据库，处方触发 |
