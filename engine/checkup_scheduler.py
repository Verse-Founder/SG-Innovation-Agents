"""
engine/checkup_scheduler.py
智能复诊调度

- 常规周期复诊提醒
- 动态提前：患者数据异常趋势 → 提前复诊建议
"""
from datetime import datetime
from schemas.health import HealthSnapshot
from utils.time_utils import days_since
from config import settings


def assess_checkup_needs(snapshot: HealthSnapshot) -> list[dict]:
    """
    评估患者是否需要复诊
    返回复诊建议列表
    """
    recommendations = []

    # ── HbA1c 定期复查 ──
    if snapshot.last_hba1c_date:
        days = days_since(snapshot.last_hba1c_date)
        if days is not None:
            if days >= settings.HBA1C_TEST_INTERVAL_DAYS:
                recommendations.append({
                    "type": "HbA1c 复查",
                    "urgency": "high",
                    "reason": f"距上次检测已 {days} 天，超过 {settings.CHECKUP_HBA1C_MONTHS} 个月周期",
                    "caring_message": f"3 个月到了呢，该去验一下 HbA1c 了。这是了解您近期"
                                      "血糖整体表现的最好方式，就像期末考试看总成绩一样 📊",
                })
            elif days >= settings.HBA1C_TEST_INTERVAL_DAYS - 14:
                recommendations.append({
                    "type": "HbA1c 复查",
                    "urgency": "medium",
                    "reason": f"距上次检测已 {days} 天，即将到期",
                    "caring_message": "快到 3 个月了，可以开始安排 HbA1c 检测了。"
                                      "早点约医生，时间更灵活哦 😊",
                })

    # ── 动态提前：血糖持续偏高 ──
    if snapshot.glucose.trend == "worsening":
        if snapshot.glucose.avg_fasting and snapshot.glucose.avg_fasting > settings.GLUCOSE_FASTING_HIGH:
            recommendations.append({
                "type": "血糖复诊",
                "urgency": "high",
                "reason": f"空腹血糖均值 {snapshot.glucose.avg_fasting} mmol/L 持续偏高且有恶化趋势",
                "caring_message": "最近血糖有些不太稳定，我觉得让医生帮您看看比较好。"
                                  "可能需要调整一下方案，这不是坏事，是更精准的照顾自己 💙",
            })

    # ── 动态提前：肾功能恶化 ──
    if snapshot.renal.egfr_trend == "declining":
        recommendations.append({
            "type": "肾功能复诊",
            "urgency": "critical" if (snapshot.renal.egfr and snapshot.renal.egfr < settings.EGFR_MILD_DECLINE) else "high",
            "reason": f"eGFR 呈下降趋势（当前 {snapshot.renal.egfr}），建议提前复查肾内科",
            "caring_message": "肾功能指标近期有些变化，这个比较重要，"
                              "建议您尽早去看看肾内科。我把近期数据帮您整理好了 🏥",
        })

    # ── 动态提前：服药率低 ──
    if snapshot.medication_adherence_pct < 70:
        recommendations.append({
            "type": "用药评估复诊",
            "urgency": "medium",
            "reason": f"近期服药率 {snapshot.medication_adherence_pct}%，可能需要医生评估是否调整用药方案",
            "caring_message": "最近吃药好像有些不规律，有时候可能是副作用或者时间"
                              "不太方便。和医生聊聊，看能不能找到更适合您的方案 💊",
        })

    # ── 黎明现象 ──
    if snapshot.glucose.has_dawn_phenomenon:
        recommendations.append({
            "type": "血糖模式复诊",
            "urgency": "medium",
            "reason": "检测到黎明现象（凌晨血糖异常升高），可能需要调整降糖药时间或剂量",
            "caring_message": "您的血糖有个 '黎明现象'，就是凌晨会莫名上升。"
                              "这个需要医生帮您调一下方案，很常见的，不用担心 🌅",
        })

    return recommendations


def get_next_checkup_date(last_date: datetime | None, interval_months: int) -> datetime | None:
    """计算下次应有的复诊日期"""
    if last_date is None:
        return None
    year = last_date.year + (last_date.month + interval_months - 1) // 12
    month = (last_date.month + interval_months - 1) % 12 + 1
    day = min(last_date.day, 28)  # 安全处理月末
    return last_date.replace(year=year, month=month, day=day)
