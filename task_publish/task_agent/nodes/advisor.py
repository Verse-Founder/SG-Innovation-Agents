import json
import re
import logging
from datetime import date
from typing import Dict, Any

from task_publish.task_agent.state import AgentState
from task_publish.config import settings
import redis as pyredis

# Setup redis client (this should be properly managed in a prod environment)
redis = pyredis.from_url(settings.redis_url, decode_responses=True)

logger = logging.getLogger(__name__)

def _extract_json(text: str) -> dict:
    """Robustly extract a JSON object from model output, even if wrapped in markdown code fences."""
    if not text:
        raise ValueError("Empty response text from LLM")
    
    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    text = re.sub(r'^```[a-zA-Z]*\n?', '', text.strip(), flags=re.MULTILINE)
    text = re.sub(r'```$', '', text.strip(), flags=re.MULTILINE)
    
    # Advanced extraction: find the first { and the last }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        json_str = text[start:end+1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as jde:
            # Fallback for minor JSON errors: try literal evaluations if needed or just re-raise
            raise ValueError(f"JSON decode error: {jde}. Raw snippet: {json_str[:100]}")
            
    raise ValueError(f"No JSON object found in model output: {text[:200]}")

ADVISOR_SYSTEM_PROMPT = """Exercise advisor for a diabetes app. Respond ONLY with JSON.

Input fields: calorie_deficit, recommended_duration_min, bg_status, avg_bg_last_2h, history_session_count, avg_cal_per_min, selected_park_name, selected_park_distance_m.

Reasoning rules:
1. avg_bg_last_2h < 4.5 → intensity="light", duration=20, include snack_before_exercise (15g fast carbs).
2. history_session_count >= 3 → duration = round(calorie_deficit / avg_cal_per_min), clamp [15,60].
3. history_session_count < 3 → use recommended_duration_min, confidence="low".
4. bg_status="elevated" → intensity="moderate".
5. selected_park_distance_m > 1500 → add 10 min.

Output (valid JSON only):
{"exercise_type":"walking","duration_min":<int>,"intensity":"light"|"moderate","personalized_tip":"<1 sentence>","snack_before_exercise":"<food+qty>"|null,"confidence":"low"|"medium"|"high","reasoning":"<2 sentences>"}"""

async def advisor_node(state: AgentState) -> Dict[str, Any]:
    from task_publish.task_agent.llm import llm_advisor
    import time as _time
    _t0 = _time.time()
    logger.info(f"[{_time.strftime('%H:%M:%S')}] [Advisor] ENTER user={state.get('user_id')}")

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
        advice = _extract_json(response.text)
        
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
