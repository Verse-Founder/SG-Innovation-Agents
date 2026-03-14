import json
import logging
from datetime import date
from typing import Dict, Any

from task_publish.task_agent.state import AgentState
from task_publish.config import settings
import redis as pyredis

# Setup redis client (this should be properly managed in a prod environment)
redis = pyredis.from_url(settings.redis_url, decode_responses=True)

logger = logging.getLogger(__name__)

ADVISOR_SYSTEM_PROMPT = """# Identity
You are an exercise advisor embedded in a diabetes management app.
Your role is to recommend a personalised walking exercise based on the
user's current health snapshot. You are supportive and practical,
not clinical. You do not diagnose or prescribe medication.

# What you receive
You will receive a compact JSON health snapshot with these fields:
- calorie_deficit: kcal the user still needs to burn today
- recommended_duration_min: estimate derived from user's exercise history
- bg_status: text label for current blood glucose level
- avg_bg_last_2h: numeric BG value in mmol/L (may be null)
- history_session_count: how many past exercise sessions we have data for
- avg_cal_per_min: user's personal burn rate from history (may be null)
- selected_park_name: where the user is going
- selected_park_distance_m: distance to park in metres

# Reasoning rules (apply in order)
1. If avg_bg_last_2h is not null and avg_bg_last_2h < 4.5:
   - Set intensity to "light" regardless of deficit
   - Cap duration at 20 minutes
   - Include a snack_before_exercise suggestion (15g fast carbs)
2. If history_session_count >= 3:
   - Use avg_cal_per_min to compute duration: calorie_deficit / avg_cal_per_min
   - Round to nearest 5 minutes, min 15, max 60
3. If history_session_count < 3:
   - Use recommended_duration_min from the snapshot directly
   - Set confidence to "low" in your output
4. If bg_status is "elevated":
   - Increase intensity to "moderate" (walking pace picks up)
   - Do not increase duration
5. Distance adjustment:
   - If selected_park_distance_m > 1500: add 10 minutes for travel

# Output format
Respond ONLY with a valid JSON object. No markdown, no explanation.
{
  "exercise_type": "walking",
  "duration_min": <int>,
  "intensity": "light" | "moderate",
  "personalized_tip": "<1 sentence, specific to this user's BG and history>",
  "snack_before_exercise": "<specific food + quantity>" | null,
  "confidence": "low" | "medium" | "high",
  "reasoning": "<2 sentences max explaining the key logic>"
}"""

async def advisor_node(state: AgentState) -> Dict[str, Any]:
    from task_publish.task_agent.llm import llm_advisor

    summary = state["health_summary"]

    # Check Redis cache before calling LLM
    cache_key = (f"advisor:{state['user_id']}:"
                 f"{date.today().isoformat()}:"
                 f"{summary['selected_park_name']}")
    
    try:
        cached = redis.get(cache_key)
        if cached:
            return {"exercise_advice": json.loads(cached)}
    except Exception as e:
        logger.warning(f"Redis cache access error: {e}")
        cached = None

    user_prompt = f"""Health snapshot for {summary["user_name"]}:
{json.dumps({k: v for k, v in summary.items() if k != "user_name"}, indent=2)}

Recommend a walking exercise for this user going to {summary["selected_park_name"]}."""

    try:
        response = await llm_advisor.acomplete(
            system=ADVISOR_SYSTEM_PROMPT,
            user=user_prompt,
        )
        advice = json.loads(response.text)
        
        try:
            redis.setex(cache_key, 86400, json.dumps(advice))  # TTL = 24h
        except Exception as e:
            logger.warning(f"Redis cache set error: {e}")
            
        return {"exercise_advice": advice}

    except Exception as e:
        logger.error(f"advisor_node error: {str(e)}")
        # Rule-based fallback: use recommended_duration from Analyst
        return {"exercise_advice": {
            "exercise_type":       "walking",
            "duration_min":        summary["recommended_duration_min"],
            "intensity":           "light",
            "personalized_tip":    "A gentle walk will help keep your glucose stable.",
            "snack_before_exercise": None,
            "confidence":          "low",
            "reasoning":           "Fallback: LLM unavailable.",
        }}
