"""
engine/intelligence.py
🧠 TaskIntelligenceEngine — 统一智能引擎

使用 SEA-LION 推理模型作为 AI 医学顾问：
- 分析患者健康快照 + 行为模式 + 聊天记录
- 输出风险评估 + 个性化任务建议
- 动态场景发现（不限于硬编码规则）
"""
import json
from schemas.health import HealthSnapshot, BehaviorPattern
from schemas.task import RiskAssessment
from utils.llm_factory import call_sealion
from config import settings


MEDICAL_ADVISOR_SYSTEM_PROMPT = """你是一位资深的新加坡糖尿病专科护理顾问（Diabetes Nurse Specialist），
服务于本地慢性病患者。你的职责是根据患者数据进行全面的健康风险评估并提出个性化的任务建议。

你必须回复严格的 JSON 格式，不要有任何额外文字。JSON 结构如下：
{
    "risk_level": "critical/high/medium/low",
    "risks": [
        {"type": "低血糖/高血糖/肾功能/用药/复诊/...", "severity": "high/medium/low", "description": "..."}
    ],
    "recommended_tasks": [
        {
            "category": "exercise/diet/medication/monitoring/checkup/renal",
            "title": "任务标题",
            "description": "详细说明",
            "caring_message": "温暖有人文关怀的提示语（像朋友一样说话，不要像医生命令）",
            "priority": "critical/high/medium/low",
            "points": 5
        }
    ],
    "requires_doctor_review": true/false,
    "renal_concern": true/false,
    "checkup_recommendation": "如有需要，说明建议的复诊类型和时间" 或 null,
    "weekly_focus": "本周建议重点关注的方向（一句话概括）"
}

核心原则：
1. 温暖关怀：caring_message 必须像朋友说话，用鼓励式话术。
   - 好的例子："如果你现在动一动10分钟，预测明天早上空腹血糖能降0.5mmol/L，就可以多喝一碗豆浆☀️"
   - 坏的例子："请立即运动以降低血糖"
2. 降低门槛：把大任务拆成小步骤，强调即时好处。
3. 新加坡本地化：饮食建议用本地食物（鸡饭、叻沙、椰浆饭等），提供低GI替代方案。
4. 肾功能关注：eGFR下降趋势、泡沫尿、蛋白尿是重要警报。
5. 用药安全：用药调整必须标记 requires_doctor_review=true，不得直接建议改药量。
6. 运动处方安全：血糖<4.4不运动需先补餐，血糖>16.7禁运动，血压>160/100禁运动。
7. 结合聊天记录：用户在聊天中透露的症状、情绪、饮食情况是重要参考。
"""


def build_patient_data_prompt(
    snapshot: HealthSnapshot,
    behavior: BehaviorPattern,
    chat_insights: list[str] | None = None,
) -> str:
    """构建患者数据 prompt"""
    # 血糖数据
    glucose_readings = ""
    for r in snapshot.glucose.recent_readings[-6:]:
        glucose_readings += f"  - {r.timestamp.strftime('%H:%M')} [{r.context}]: {r.value} mmol/L\n"

    # 用餐数据
    meals_text = ""
    for m in snapshot.today_meals:
        meals_text += f"  - {m.meal_type}: {m.description}"
        if m.estimated_calories:
            meals_text += f" (~{m.estimated_calories}kcal, GI:{m.gi_level})"
        meals_text += "\n"

    # 用药数据
    meds_text = ""
    for med in snapshot.today_medications:
        status = "✅已服用" if med.taken else "❌未服用"
        meds_text += f"  - {med.medication_name} {med.scheduled_time}: {status}\n"

    # 聊天摘要
    chat_text = ""
    if chat_insights:
        for insight in chat_insights[-5:]:
            chat_text += f"  - {insight}\n"

    # 症状
    symptoms_text = "无" if not snapshot.reported_symptoms else "、".join(snapshot.reported_symptoms)

    return f"""
【患者健康快照】
- 用户ID: {snapshot.user_id}
- 当前情绪: {snapshot.emotional_state}
- 自报症状: {symptoms_text}

【血糖数据】
- 趋势: {snapshot.glucose.trend}
- 黎明现象: {"是" if snapshot.glucose.has_dawn_phenomenon else "否"}
- 空腹均值: {snapshot.glucose.avg_fasting or "N/A"} mmol/L
- 餐后均值: {snapshot.glucose.avg_post_meal or "N/A"} mmol/L
- TIR: {snapshot.glucose.time_in_range_pct or "N/A"}%
- 最近读数:
{glucose_readings}
【HbA1c】
- 最新值: {snapshot.latest_hba1c or "N/A"}% (目标 <{settings.HBA1C_TARGET}%)
- 测量日期: {snapshot.last_hba1c_date.strftime('%Y-%m-%d') if snapshot.last_hba1c_date else "N/A"}

【肾功能】
- eGFR: {snapshot.renal.egfr or "N/A"} mL/min/1.73m² (前次: {snapshot.renal.egfr_previous or "N/A"})
- 趋势: {snapshot.renal.egfr_trend}
- 蛋白尿: {snapshot.renal.proteinuria or "未测"} mg/day
- 泡沫尿: {"有" if snapshot.renal.has_foam_urine else "无"}

【今日用餐】
{meals_text or "  无记录"}
【今日用药】
{meds_text or "  无记录"}
【今日运动】
- 步数: {snapshot.today_steps}
- 常规运动时间: {snapshot.usual_exercise_time or "未设置"}
- 活动记录: {len(snapshot.today_exercise)} 次

【生命体征】
- 心率: {snapshot.heart_rate or "N/A"} bpm
- 血压: {snapshot.blood_pressure_sys or "N/A"}/{snapshot.blood_pressure_dia or "N/A"} mmHg

【行为模式（上周）】
- 周均步数: {behavior.avg_daily_steps}
- 运动天数: {behavior.exercise_days_per_week}/7
- 服药率: {behavior.medication_adherence_pct}%
- 任务完成率: {behavior.task_completion_rate * 100:.0f}%
- 连续完成天数: {behavior.consecutive_completion_days}
- 血糖控制评分: {behavior.glucose_control_score * 100:.0f}/100

【聊天记录摘要】
{chat_text or "  无"}
【复诊记录】
- 上次复诊: {snapshot.last_checkup_date.strftime('%Y-%m-%d') if snapshot.last_checkup_date else "N/A"}
- 下次预约: {snapshot.next_scheduled_checkup.strftime('%Y-%m-%d') if snapshot.next_scheduled_checkup else "未预约"}
"""


def analyze_and_generate_tasks(
    snapshot: HealthSnapshot,
    behavior: BehaviorPattern,
    chat_insights: list[str] | None = None,
) -> tuple[RiskAssessment, list[dict]]:
    """
    核心方法：AI 医学顾问分析患者数据，输出风险评估 + 个性化任务
    返回 (RiskAssessment, recommended_tasks list)
    """
    patient_data = build_patient_data_prompt(snapshot, behavior, chat_insights)

    raw_response = call_sealion(
        system_prompt=MEDICAL_ADVISOR_SYSTEM_PROMPT,
        user_message=patient_data,
        reasoning=True,  # 使用推理模型
    )

    try:
        # 清理 JSON
        clean = raw_response.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()

        data = json.loads(clean)

        risk_assessment = RiskAssessment(
            risk_level=data.get("risk_level", "low"),
            risks=data.get("risks", []),
            recommended_actions=[t.get("title", "") for t in data.get("recommended_tasks", [])],
            requires_doctor_review=data.get("requires_doctor_review", False),
            renal_concern=data.get("renal_concern", False),
            checkup_recommendation=data.get("checkup_recommendation"),
        )

        tasks = data.get("recommended_tasks", [])

        print(f"[Intelligence] 风险等级: {risk_assessment.risk_level} | "
              f"生成任务: {len(tasks)} 个 | 需医生审核: {risk_assessment.requires_doctor_review}")
        return risk_assessment, tasks

    except (json.JSONDecodeError, KeyError) as e:
        print(f"[Intelligence] LLM 响应解析失败: {e}，使用规则引擎回退")
        return _rule_based_fallback(snapshot, behavior)


def _rule_based_fallback(
    snapshot: HealthSnapshot,
    behavior: BehaviorPattern,
) -> tuple[RiskAssessment, list[dict]]:
    """规则引擎回退：当 LLM 不可用时的基础分析"""
    risks = []
    tasks = []
    risk_level = "low"
    requires_doctor = False
    renal_concern = False

    latest_glucose = None
    if snapshot.glucose.recent_readings:
        latest_glucose = snapshot.glucose.recent_readings[-1].value

    # ── 低血糖风险 ──
    if latest_glucose and latest_glucose < settings.GLUCOSE_PRE_EXERCISE_MIN:
        risks.append({"type": "低血糖", "severity": "high",
                       "description": f"最新血糖 {latest_glucose} mmol/L 偏低"})
        tasks.append({
            "category": "diet",
            "title": "运动前补充食物",
            "description": f"您的血糖目前是 {latest_glucose} mmol/L，运动前请先吃点东西。",
            "caring_message": "先吃个小点心垫垫肚子吧，半杯牛奶或者两片全麦饼干就好，"
                              "等15分钟血糖稳定了再动也不迟 ☺️",
            "priority": "high",
            "points": 5,
        })
        risk_level = "high"

    # ── 高血糖风险 ──
    if latest_glucose and latest_glucose > settings.GLUCOSE_HIGH_THRESHOLD:
        risks.append({"type": "高血糖", "severity": "high",
                       "description": f"最新血糖 {latest_glucose} mmol/L 偏高"})
        if latest_glucose <= settings.GLUCOSE_CRITICAL_HIGH:
            tasks.append({
                "category": "exercise",
                "title": "饭后散步15分钟",
                "description": "饭后轻度运动有助于降低血糖。",
                "caring_message": "吃完饭后出去走走吧，就在楼下走15分钟就好，"
                                  "研究表明这可以让餐后血糖降低 1-2 mmol/L 呢 💪",
                "priority": "high",
                "points": 10,
            })
        risk_level = "high" if risk_level != "critical" else "critical"

    # ── 漏服药物 ──
    missed_meds = [m for m in snapshot.today_medications if not m.taken]
    if missed_meds:
        for med in missed_meds:
            risks.append({"type": "用药", "severity": "medium",
                           "description": f"{med.medication_name} 未按时服用"})
            tasks.append({
                "category": "medication",
                "title": f"服药提醒：{med.medication_name}",
                "description": f"您今天的 {med.medication_name} 还没吃。",
                "caring_message": f"提醒一下，今天的 {med.medication_name} 还没吃哦。"
                                  "按时吃药是控糖最重要的基石，加油 💊",
                "priority": "high",
                "points": 10,
            })

    # ── 肾功能 ──
    if snapshot.renal.egfr and snapshot.renal.egfr < settings.EGFR_MILD_DECLINE:
        renal_concern = True
        risks.append({"type": "肾功能", "severity": "high",
                       "description": f"eGFR {snapshot.renal.egfr} 低于正常范围"})
        tasks.append({
            "category": "renal",
            "title": "肾功能检查提醒",
            "description": "您的肾功能指标需要关注，建议尽快复诊。",
            "caring_message": "最近的肾功能指标有些变化，这个很重要需要医生帮您看看。"
                              "我帮您整理好了数据，带着去看医生会方便很多 🏥",
            "priority": "critical",
            "points": 15,
        })
        requires_doctor = True
        risk_level = "critical"

    if snapshot.renal.has_foam_urine:
        renal_concern = True
        risks.append({"type": "肾功能", "severity": "medium",
                       "description": "报告泡沫尿，可能提示蛋白尿"})

    # ── 复诊提醒 ──
    checkup_rec = None
    if snapshot.last_hba1c_date:
        from utils.time_utils import days_since
        days = days_since(snapshot.last_hba1c_date)
        if days and days > settings.HBA1C_TEST_INTERVAL_DAYS - 14:
            checkup_rec = f"距上次 HbA1c 检测已 {days} 天，建议近期复查"
            tasks.append({
                "category": "checkup",
                "title": "HbA1c 复查提醒",
                "description": f"距上次 HbA1c 检测已 {days} 天。",
                "caring_message": "快到3个月了，该测一下 HbA1c 了。"
                                  "定期检查是最好的健康投资，可以让我帮您预约吗？😊",
                "priority": "medium",
                "points": 10,
            })

    risk_assessment = RiskAssessment(
        risk_level=risk_level,
        risks=risks,
        recommended_actions=[t["title"] for t in tasks],
        requires_doctor_review=requires_doctor,
        renal_concern=renal_concern,
        checkup_recommendation=checkup_rec,
    )

    print(f"[Intelligence/Fallback] 风险等级: {risk_level} | 任务: {len(tasks)} 个")
    return risk_assessment, tasks
