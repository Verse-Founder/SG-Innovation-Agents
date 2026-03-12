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


def calculate_metabolic_metrics(snapshot: HealthSnapshot) -> dict:
    """计算 BMI 和心率区间"""
    bmi = None
    if snapshot.height_cm and snapshot.weight_kg:
        bmi = snapshot.weight_kg / ((snapshot.height_cm / 100) ** 2)
    
    hr_zones = None
    if snapshot.age:
        max_hr = 220 - snapshot.age
        hr_zones = {
            "max_hr": max_hr,
            "zone1": (int(max_hr * 0.5), int(max_hr * 0.6)),
            "zone2": (int(max_hr * 0.6), int(max_hr * 0.7)),
            "zone3": (int(max_hr * 0.7), int(max_hr * 0.8)),
        }
    
    return {"bmi": bmi, "hr_zones": hr_zones}


MEDICAL_ADVISOR_SYSTEM_PROMPT = """你是一位资深的新加坡糖尿病专科护理顾问（Diabetes Nurse Specialist）。
你的职责是根据患者数据进行全面的健康风险评估并提出个性化的任务建议。

核心运动指南参考：
1. 循序渐进：从低强度开始，避免突然剧烈运动。以“微喘但能说话”为度。
2. 规律坚持：每周至少150分钟中等强度有氧运动（平均每天30分钟，5天）。
3. 组合模式：有氧运动（控糖主力）+ 抗阻运动（增加肌肉提高代谢）+ 柔韧性/平衡训练（防跌倒）。
4. 风险规避：餐后1-2小时运动最佳。避开打完胰岛素/服药后马上开展高强度运动。
5. 安全红线：血糖 < 4.4 不运动需补充 15g 碳水；血糖 > 16.7 禁运动；收缩压 > 160 禁运动。

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
2. 降低门槛：把大任务拆成小步骤，强调即时好处。
3. 新加坡本地化：建议低GI替代方案（如糙米、少糖 kopi-o）。
4. 运动建议：建议应包含具体的卡路里消耗目标或分钟数。
"""


def build_patient_data_prompt(
    snapshot: HealthSnapshot,
    behavior: BehaviorPattern,
    chat_insights: list[str] | None = None,
    nearby_parks: list[dict] | None = None,
) -> str:
    """构建患者数据 prompt，包含代谢和位置信息"""
    # 血糖数据
    glucose_readings = ""
    for r in snapshot.glucose.recent_readings[-6:]:
        glucose_readings += f"  - {r.timestamp.strftime('%H:%M')} [{r.context}]: {r.value} mmol/L\n"

    # 代谢计算
    meta = calculate_metabolic_metrics(snapshot)
    bmi_text = f"{meta['bmi']:.1f}" if meta["bmi"] else "N/A"
    
    hr_zones = "N/A"
    if meta["hr_zones"]:
        z = meta["hr_zones"]
        hr_zones = (
            f"1区(热身): {z['zone1'][0]}-{z['zone1'][1]}, "
            f"2区(燃脂): {z['zone2'][0]}-{z['zone2'][1]}, "
            f"3区(有氧): {z['zone3'][0]}-{z['zone3'][1]}"
        )

    # 聊天摘要
    chat_text = ""
    if chat_insights:
        for insight in chat_insights[-5:]:
            chat_text += f"  - {insight}\n"

    # 公园推荐
    parks_text = "未提供或周围无公园"
    if nearby_parks:
        parks_text = "\n".join([f"  - {p['name']} (GPS: {p['latitude']},{p['longitude']})" for p in nearby_parks])

    # 症状
    symptoms_text = "无" if not snapshot.reported_symptoms else "、".join(snapshot.reported_symptoms)

    # 详细运动量
    exercise_details = ""
    for ex in snapshot.today_exercise:
        start_str = ex.start_time.strftime("%H:%M") if ex.start_time else "N/A"
        exercise_details += f"  - {ex.exercise_type}: {ex.calories_burned} kcal ({ex.duration_min} min, {start_str}, HR: {ex.avg_heart_rate})\n"

    # 肾功能
    renal_text = f"eGFR: {snapshot.renal.egfr or 'N/A'}, 蛋白尿: {snapshot.renal.proteinuria or 'N/A'}, 趋势: {snapshot.renal.egfr_trend}"

    return f"""
【患者基础信息】
- 用户 ID: {snapshot.user_id}
- BMI: {bmi_text} (身高: {snapshot.height_cm}cm, 体重: {snapshot.weight_kg}kg)
- 患者年龄: {snapshot.age or "N/A"}
- 目标心率区间: {hr_zones}

【附近可运动地点】
{parks_text}

【患者健康快照】
- 自报症状: {symptoms_text}
- 情绪状态: {snapshot.emotional_state}

【血糖数据】
{glucose_readings or "  无近期数据"}
- 趋势: {snapshot.glucose.trend}
- TIR: {snapshot.glucose.time_in_range_pct or "N/A"}%

【肾功能】
- {renal_text}
- 泡沫尿: {"有" if snapshot.renal.has_foam_urine else "无"}

【HbA1c】
- 最新值: {snapshot.latest_hba1c or "N/A"}%

【今日状态】
- 今日消耗: {snapshot.today_calories} kcal
- 运动记录: {len(snapshot.today_exercise)} 次
{exercise_details or "  无"}
- 最新心率: {snapshot.heart_rate or "N/A"} bpm
- 血压: {snapshot.blood_pressure_sys}/{snapshot.blood_pressure_dia} mmHg

【行为模式（上周连击）】
- 连击天数: {behavior.current_streak_days} 天
- 周均每日消耗: {behavior.avg_daily_calories} kcal
- 建议运动时间: {behavior.exercise_preferred_time}

【聊天记录摘要】
{chat_text or "  无"}
"""


def analyze_and_generate_tasks(
    snapshot: HealthSnapshot,
    behavior: BehaviorPattern,
    chat_insights: list[str] | None = None,
    nearby_parks: list[dict] | None = None,
) -> tuple[RiskAssessment, list[dict]]:
    """
    核心方法：AI 医学顾问分析患者数据，输出风险评估 + 个性化任务
    """
    patient_data = build_patient_data_prompt(snapshot, behavior, chat_insights, nearby_parks)

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

    # ── 运动量监测 ──
    if snapshot.today_calories < settings.DEFAULT_DAILY_CALORIES_GOAL:
        gap = settings.DEFAULT_DAILY_CALORIES_GOAL - snapshot.today_calories
        tasks.append({
            "category": "exercise",
            "title": "今日运动达标挑战",
            "description": f"您今天已消耗 {snapshot.today_calories} kcal，距离目标还差 {gap} kcal。",
            "caring_message": f"今天已经动了动，很棒哦！再稍微加一把劲消耗 {gap} kcal，"
                              "大概就是散步 15 分钟的事儿，要不要下楼吹吹风？🌳",
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

    print(f"[Intelligence/Fallback] 风险等级: {risk_level} | 任务: {len(tasks)} 个 | 消耗: {snapshot.today_calories} kcal")
    return risk_assessment, tasks
