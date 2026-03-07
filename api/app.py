"""
api/app.py
FastAPI 应用（对标 Julia 的 diabetes-guardian）
"""
from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="Task Agent | 糖尿病健康任务管理",
    description="SG Innovation Challenge — 个性化任务发布Agent",
    version="1.0.0",
)
app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "task-agent"}
