from task_publish.task_agent.state import AgentState
from typing import Dict, Any

async def analyst_node(state: AgentState) -> Dict[str, Any]:
    profile  = state["user_profile"]
    rule_res = state["rule_result"]
    history  = state["exercise_history"] or []
    park     = state["selected_park"]

    # Compute historical drop average for same exercise type
    # exercise_history items: {type, duration_min, calories_burned}
    # We infer caloric efficiency: calories_burned / duration_min
    efficiencies = [
        h["calories_burned"] / h["duration_min"]
        for h in history
        if h.get("duration_min") and h.get("calories_burned")
    ]
    avg_cal_per_min = round(sum(efficiencies)/len(efficiencies), 2) if efficiencies else None

    # Estimate recommended duration from deficit
    deficit = rule_res["deficit_kcal"]
    if avg_cal_per_min and avg_cal_per_min > 0:
        recommended_duration = max(15, round(deficit / avg_cal_per_min))
    else:
        # Fallback: ADA standard 150 min/week -> ~21 min/day
        recommended_duration = 21

    # BG trend label
    bg = state.get("avg_bg_last_2h")
    if bg is None:
        bg_status = "unknown"
    elif bg < 4.0:
        bg_status = "low (caution)"
    elif bg < 5.6:
        bg_status = "slightly low"
    elif bg <= 10.0:
        bg_status = "normal"
    else:
        bg_status = "elevated"

    health_summary = {
        "user_name":              profile["name"],
        "bmi":                    profile["bmi"],
        "calories_burned_today":  state["calories_burned_today"] or 0,
        "calorie_deficit":        deficit,
        "recommended_duration_min": recommended_duration,
        "bg_status":              bg_status,
        "avg_bg_last_2h":         bg,
        "history_session_count":  len(history),
        "avg_cal_per_min":        avg_cal_per_min,
        "selected_park_name":     park["name"],
        "selected_park_distance_m": park["distance_m"],
        "language_pref":          profile.get("language_pref", "en"),
    }

    return {"health_summary": health_summary}
