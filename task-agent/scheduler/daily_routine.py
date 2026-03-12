"""
scheduler/daily_routine.py
日常固定任务推送 — 纯调度逻辑，不走 Agent 图
"""
import logging
import random
from datetime import datetime, timedelta, timezone

from config import settings
from utils.llm_factory import call_sealion
import json

logger = logging.getLogger(__name__)

# ── 糖尿病知识题库 ──────────────────────────────────────
QUIZ_BANK = [
    {
        "question": "糖尿病患者运动前血糖低于多少 mmol/L 时需要先补充碳水？",
        "options": ["3.9", "4.4", "5.6", "7.0"],
        "answer": "5.6",
        "explanation": "运动前血糖低于 5.6 mmol/L 建议先补充 15-20g 碳水化合物再运动。",
    },
    {
        "question": "HbA1c 检测建议多长时间做一次？",
        "options": ["每月", "每 3 个月", "每 6 个月", "每年"],
        "answer": "每 3 个月",
        "explanation": "HbA1c 反映过去 2-3 个月的平均血糖水平，因此建议每 3 个月检测一次。",
    },
    {
        "question": "以下哪种运动最适合糖尿病患者日常进行？",
        "options": ["高强度间歇训练", "快步走", "举重", "短跑"],
        "answer": "快步走",
        "explanation": "快步走是中等强度有氧运动，安全且有效降低血糖，建议每周至少 150 分钟。",
    },
    {
        "question": "eGFR 值低于多少表示中度肾功能下降？",
        "options": ["90", "60", "45", "30"],
        "answer": "45",
        "explanation": "eGFR 在 45-59 之间为轻-中度下降，低于 45 为中度下降，需加强监测。",
    },
    {
        "question": "糖尿病患者每日推荐步数目标是多少步？",
        "options": ["3000", "5000", "6000", "10000"],
        "answer": "6000",
        "explanation": "研究表明每日 6000 步即可有效改善血糖控制，同时不至于对关节造成过大负担。",
    },
    {
        "question": "餐后 2 小时血糖超过多少 mmol/L 属于偏高？",
        "options": ["7.0", "7.8", "10.0", "11.1"],
        "answer": "10.0",
        "explanation": "餐后 2 小时血糖超过 10.0 mmol/L 表明血糖控制不佳，需调整饮食或药物。",
    },
    {
        "question": "低血糖的典型症状不包括以下哪项？",
        "options": ["手抖", "出冷汗", "精力充沛", "心跳加速"],
        "answer": "精力充沛",
        "explanation": "低血糖典型症状包括手抖、出冷汗、心跳加速、头晕，精力充沛并非低血糖表现。",
    },
    {
        "question": "泡沫尿可能提示什么健康问题？",
        "options": ["脱水", "蛋白尿（肾功能损伤）", "高血糖", "运动过量"],
        "answer": "蛋白尿（肾功能损伤）",
        "explanation": "持续性泡沫尿可能是蛋白尿的表现，提示肾小球滤过功能受损，需进一步检查。",
    },
]

# ── 温暖话术模板 ────────────────────────────────────────
CARING_MESSAGES = {
    "steps": [
        "今天也一起动起来吧！哪怕是楼下散步 10 分钟也很棒哦 🚶‍♀️",
        "身体喜欢被温柔对待~来一段轻松的散步吧 ☀️",
        "每一步都算数！今天的目标是 {goal} 步，你能行的 💪",
    ],
    "meal": {
        "breakfast": "早安呀！记得拍一下早餐照片哦 📸 均衡的早餐是美好一天的开始～",
        "lunch": "午饭时间到！拍张照片让我看看你今天吃了什么好吃的 🍱",
        "dinner": "辛苦一天了！记录晚餐，保持好习惯 🌙 拍张照片就好～",
    },
    "quiz": [
        "来挑战今天的健康小问答吧 🧠 只需 1 分钟！",
        "每天学一点，健康多一点 💡 今日一题等你来～",
    ],
    "medication": "该吃药了哦 💊 按时服药，才能让身体稳稳当当的。你做得很好！",
    "glucose": "记得测一下血糖哦 🩸 了解自己的身体状态，才能更好地照顾自己～",
    "hba1c": "距离上次 HbA1c 检测已经 3 个月了，建议预约一次检查 🏥 这是了解长期血糖控制的好方法！",
}


def _make_task_dict(
    *,
    user_id: str,
    task_type: str = "daily_routine",
    category: str,
    title: str,
    description: str,
    caring_message: str = "",
    points: int = 5,
    priority: str = "low",
    deadline_hours: int = 24,
    metadata: dict | None = None,
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "task_type": task_type,
        "category": category,
        "title": title,
        "description": description,
        "caring_message": caring_message,
        "points": points,
        "priority": priority,
        "deadline": now + timedelta(hours=deadline_hours),
        "trigger_source": "cron",
        "metadata": metadata,
    }


def generate_daily_tasks(user_id: str = "all") -> list[dict]:
    """生成一天的固定任务"""
    tasks = []
    goal = settings.DEFAULT_DAILY_CALORIES_GOAL
    msg = random.choice(CARING_MESSAGES["steps"]).format(goal=goal)
    tasks.append(_make_task_dict(
        user_id=user_id, category="exercise",
        title="今日消耗打卡",
        description=f"目标：{goal} kcal。轻到中等强度的运动就很好！",
        caring_message=msg, points=settings.POINTS_DAILY_EXERCISE,
    ))
    tasks.append(_make_task_dict(
        user_id=user_id, category="monitoring",
        title="血糖监测",
        description="请记录您的血糖数值（空腹或餐后均可）。",
        caring_message=CARING_MESSAGES["glucose"], points=5,
    ))
    tasks.append(_make_task_dict(
        user_id=user_id, category="medication",
        title="按时服药提醒",
        description="请按照医嘱按时服药，保持规律。",
        caring_message=CARING_MESSAGES["medication"],
        points=settings.POINTS_MEDICATION_ON_TIME,
    ))
    return tasks


def generate_meal_photo_task(user_id: str, meal: str) -> dict:
    meal_cn = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐"}.get(meal, meal)
    return _make_task_dict(
        user_id=user_id, category="diet",
        title=f"{meal_cn}照片打卡",
        description=f"拍一张您的{meal_cn}照片，方便我们分析膳食营养。",
        caring_message=CARING_MESSAGES["meal"].get(meal, "记得拍照哦～"),
        points=settings.POINTS_MEAL_PHOTO, deadline_hours=4,
    )


def generate_ai_quiz(user_id: str) -> dict:
    """调用 LLM 生成个性化的糖尿病知识问答"""
    prompt = """你是一位专业的糖尿病健康管理专家。请生成一道关于糖尿病日常管理的单项选择题。
    要求：
    1. 结合新加坡本地语境（如：Hawker Center 饮食、HDB 运动场景）。
    2. 提供 4 个选项。
    3. 语言像好朋友一样幽默、温暖。
    4. 必须输出严格的 JSON 格式，不要包含反斜杠或额外描述：
    {
      "question": "问题内容",
      "options": ["选A", "选B", "选C", "选D"],
      "answer": "正确选项内容",
      "explanation": "通俗易懂的原理解释"
    }
    """
    try:
        response = call_sealion(
            system_prompt=prompt,
            user_message="请为今天生成一道糖尿病小知识题。",
            reasoning=False
        )
        # 清理可能存在的 markdown fence
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        quiz_data = json.loads(clean)
        
        return _make_task_dict(
            user_id=user_id, category="quiz",
            title="每日挑战：AI 懂糖小课堂",
            description=quiz_data["question"],
            caring_message=random.choice(CARING_MESSAGES["quiz"]),
            points=settings.POINTS_DAILY_QUIZ,
            metadata={
                "quiz_options": quiz_data["options"],
                "quiz_answer": quiz_data["answer"],
                "quiz_explanation": quiz_data["explanation"],
            }
        )
    except Exception as e:
        logger.error(f"AI 出题失败: {e}，回退到固定题库")
        return generate_daily_quiz_static(user_id)


def generate_daily_quiz_static(user_id: str) -> dict:
    """原本的静态题库逻辑作为兜底"""
    quiz = random.choice(QUIZ_BANK)
    return _make_task_dict(
        user_id=user_id, category="quiz",
        title="每日一题：糖尿病知识",
        description=quiz["question"],
        caring_message=random.choice(CARING_MESSAGES["quiz"]),
        points=settings.POINTS_DAILY_QUIZ, deadline_hours=24,
        metadata={
            "quiz_options": quiz["options"],
            "quiz_answer": quiz["answer"],
            "quiz_explanation": quiz["explanation"],
        },
    )


def generate_hba1c_reminder(user_id: str) -> dict:
    return _make_task_dict(
        user_id=user_id, category="checkup",
        title="HbA1c 定期检测提醒",
        description="距离上次 HbA1c 检测已满 3 个月，建议预约内分泌科复诊并检测 HbA1c。",
        caring_message=CARING_MESSAGES["hba1c"],
        points=15, priority="medium", deadline_hours=168,
    )


def generate_weekly_metrics_task(user_id: str) -> list[dict]:
    """每周一次提醒记录体重和腰围"""
    return [
        _make_task_dict(
            user_id=user_id, category="monitoring",
            title="每周体成分记录：体重",
            description="记录一下您本周的体重，帮我们更好地计算 BMI。",
            caring_message="体重只是一个数字，重要的是我们一起保持进步 🌱",
            points=10, priority="medium", deadline_hours=48,
        ),
        _make_task_dict(
            user_id=user_id, category="monitoring",
            title="每周体成分记录：腰围",
            description="记录一下您本周的腰围。腰围对评估腹部脂肪很重要哦。",
            caring_message="关注健康细节，也是爱自己的表现 ❤️",
            points=10, priority="medium", deadline_hours=48,
        )
    ]


# ── Celery Tasks ─────────────────────────────────────────
try:
    from scheduler.celery_app import celery_app

    @celery_app.task(name="scheduler.daily_routine.push_daily_tasks")
    def push_daily_tasks():
        tasks = generate_daily_tasks("all")
        logger.info(f"[Scheduler] 推送 {len(tasks)} 条日常任务")
        return {"count": len(tasks)}

    @celery_app.task(name="scheduler.daily_routine.push_meal_photo_reminder")
    def push_meal_photo_reminder(meal: str = "breakfast"):
        task = generate_meal_photo_task("all", meal)
        logger.info(f"[Scheduler] 推送{meal}照片提醒")
        return {"meal": meal, "task": task["title"]}

    @celery_app.task(name="scheduler.daily_routine.push_daily_quiz")
    def push_daily_quiz():
        task = generate_ai_quiz("all")
        logger.info("[Scheduler] 推送 AI 每日一题")
        return {"task": task["title"]}

    @celery_app.task(name="scheduler.daily_routine.push_steps_reminder")
    def push_steps_reminder():
        logger.info("[Scheduler] 推送步数完成提醒")
        return {"task": "步数提醒"}

    @celery_app.task(name="scheduler.daily_routine.check_hba1c_reminder")
    def check_hba1c_reminder():
        task = generate_hba1c_reminder("all")
        logger.info("[Scheduler] 检查 HbA1c 提醒")
        return {"task": task["title"]}

    @celery_app.task(name="scheduler.daily_routine.push_weekly_metrics")
    def push_weekly_metrics():
        tasks = generate_weekly_metrics_task("all")
        logger.info(f"[Scheduler] 推送 {len(tasks)} 条周常测量任务")
        return {"count": len(tasks)}

    @celery_app.task(name="scheduler.daily_routine.daily_streak_check")
    def daily_streak_check():
        """
        每日凌晨核对前一日任务完成状态，更新/重置连击
        """
        logger.info("[Scheduler] 开始执行每日连击检查 (Streak Check)")
        # 实际逻辑应为：
        # 1. 遍历活跃用户
        # 2. 调用 points_engine.check_and_update_streak(user_id)
        return {"status": "logic_updated"}

except ImportError:
    logger.warning("Celery 未安装，定时任务注册跳过")
