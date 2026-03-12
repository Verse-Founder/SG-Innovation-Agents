"""
main.py
Task Agent CLI 入口 — 用于本地开发测试和 Demo
"""
import sys
import json
from graph.builder import run_task_agent


def print_tasks(output: dict):
    """美化输出任务列表"""
    if not output:
        print("❌ 无输出")
        return

    batch = output.get("batch", {})
    tasks = batch.get("tasks", [])
    risk_level = output.get("risk_level", "low")
    summary = batch.get("summary", "")

    risk_emoji = {"critical": "🚨", "high": "⚠️", "medium": "💛", "low": "💚"}.get(risk_level, "ℹ️")

    print(f"\n{risk_emoji} 风险等级: {risk_level.upper()}")
    print(f"📝 {summary}")
    print("")

    if output.get("requires_doctor_review"):
        print("🏥 需要医生审核！部分建议涉及用药调整，请咨询医生。\n")

    if output.get("renal_concern"):
        print("🫘 肾功能需关注！请及时就医。\n")

    for i, task in enumerate(tasks, 1):
        priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
            task.get("priority", "low"), "⚪")
        print(f"  {i}. {priority_emoji} [{task.get('category', '')}] {task.get('title', '')}")
        print(f"     {task.get('description', '')}")
        if task.get("caring_message"):
            print(f"     💬 {task['caring_message']}")
        print(f"     积分: +{task.get('points', 0)} | 截止: {task.get('deadline', 'N/A')}")
        print()

    # 推送通知
    notifications = output.get("notifications", [])
    if notifications:
        print(f"📱 推送通知 ({len(notifications)}):")
        for n in notifications:
            print(f"  • {n.get('title', '')}: {n.get('body', '')}")
        print()


import asyncio

async def run_and_print(user_id: str, trigger_source: str, trigger_payload: dict = None):
    output = await run_task_agent(user_id, trigger_source=trigger_source, trigger_payload=trigger_payload)
    print_tasks(output)

async def main():
    """CLI 主循环"""
    print("=" * 60)
    print("🤖 Task Agent — 糖尿病个性化任务管理系统")
    print("   SG Innovation Challenge 2026")
    print("=" * 60)
    print()
    print("可用命令：")
    print("  daily       - 查看日常任务")
    print("  weekly      - 查看本周个性化任务")
    print("  risk        - 运行风险评估")
    print("  exercise    - 模拟运动前风险检查")
    print("  renal       - 模拟肾功能报告")
    print("  medication  - 模拟漏服药物场景")
    print("  chatbot     - 模拟 chatbot 转发请求")
    print("  alert       - 模拟预警 Agent 信号")
    print("  quit / q    - 退出")
    print()

    while True:
        try:
            cmd = input("task-agent> ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 再见！")
            break

        if cmd in ("quit", "q", "exit"):
            print("👋 再见！")
            break

        elif cmd == "daily":
            await run_and_print("user_001", trigger_source="cron")

        elif cmd == "weekly":
            await run_and_print("user_001", trigger_source="system",
                               trigger_payload={"type": "weekly_review"})

        elif cmd == "risk":
            await run_and_print("user_001", trigger_source="system")

        elif cmd == "exercise":
            await run_and_print("user_001", trigger_source="chatbot",
                               trigger_payload={"type": "task_request",
                                                "request": "我打算去跑步"})

        elif cmd == "renal":
            await run_and_print("user_001", trigger_source="system",
                               trigger_payload={"type": "health_check",
                                                "request": "肾功能检查"})

        elif cmd == "medication":
            await run_and_print("user_001", trigger_source="system",
                               trigger_payload={"type": "medication_check",
                                                "request": "用药提醒"})

        elif cmd == "chatbot":
            await run_and_print("user_001", trigger_source="chatbot",
                               trigger_payload={
                                   "type": "task_request",
                                   "request": "我今天想打卡，有什么任务推荐？",
                                   "user_id": "user_001",
                               })

        elif cmd == "alert":
            await run_and_print("user_001", trigger_source="alert_agent",
                               trigger_payload={
                                   "severity": "high",
                                   "type": "glucose_alert",
                                   "alert_level": "high",
                                   "message": "血糖持续偏高，需要干预",
                               })

        elif cmd:
            # 自由输入当作 chatbot 消息
            await run_and_print("user_001", trigger_source="chatbot",
                               trigger_payload={
                                   "type": "task_request",
                                   "request": cmd,
                               })


if __name__ == "__main__":
    asyncio.run(main())
