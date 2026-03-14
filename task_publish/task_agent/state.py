from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):
    # ── Input (from trigger) ────────────────────────────────────────
    user_id:              str
    trigger_source:       str          # "cron" | "bg_spike" | "admin"

    # ── ContextLoader fills ─────────────────────────────────────────
    user_profile:         Optional[Dict[str, Any]]
    # {name, weight_kg, height_cm, bmi, language_pref}
    calories_burned_today: Optional[float]
    avg_bg_last_2h:       Optional[float]
    exercise_history:     Optional[List[Dict[str, Any]]]
    # last 3 sessions of same type: [{type, duration_min, calories_burned}]
    last_gps:             Optional[Dict[str, Any]]   # {lat, lng}

    # ── RuleEngine fills ────────────────────────────────────────────
    rule:                 Optional[Dict[str, Any]]
    # {base_calorie, trigger_threshold, exercise_pts, ...}
    rule_result:          Optional[Dict[str, Any]]
    # {should_trigger, deficit_kcal, adjusted_target}

    # ── MapTool fills ───────────────────────────────────────────────
    park_candidates:      Optional[List[Dict[str, Any]]]
    # [{name, lat, lng, distance_m}, ...]  max 3

    # ── UserInteractionNode fills ───────────────────────────────────
    selected_park:        Optional[Dict[str, Any]]
    # {name, lat, lng, distance_m}

    # ── Analyst node fills ──────────────────────────────────────────
    health_summary:       Optional[Dict[str, Any]]   # HealthSummaryDTO

    # ── Advisor node fills ──────────────────────────────────────────
    exercise_advice:      Optional[Dict[str, Any]]   # ExerciseAdviceDTO

    # ── Writer node fills ───────────────────────────────────────────
    task_content:         Optional[Dict[str, Any]]
    # {title, body, cta}  in users.language_pref
