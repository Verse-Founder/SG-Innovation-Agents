import json
import re
import logging
from typing import Dict, Any

from task_publish.task_agent.state import AgentState

logger = logging.getLogger(__name__)

def _extract_json(text: str) -> dict:
    text = re.sub(r'^```[a-zA-Z]*\n?', '', text.strip(), flags=re.MULTILINE)
    text = re.sub(r'```$', '', text.strip(), flags=re.MULTILINE)
    m = re.search(r'\{[\s\S]+\}', text)
    if m:
        return json.loads(m.group())
    raise ValueError(f"No JSON object found in writer output: {text[:200]}")

WRITER_SYSTEM_PROMPT = """You are a warm, friendly health companion writing a mobile push notification
for a diabetic user. You will receive:
- The user's name
- A clinical exercise recommendation (from our advisor system)
- The destination park name and distance
- The output language (users.language_pref)

Writing rules:
1. Write ONLY in the language specified by language_pref.
   Supported: en, zh-CN, zh-TW, ms, id, th.
2. Tone: warm and conversational, like a message from a caring friend.
   Not clinical. Not commanding.
3. Always include: the park name, the recommended duration.
4. If snack_before_exercise is present, weave it in naturally.
   Example: "...maybe grab a small banana before you head out."
5. If personalized_tip is present, include its essence (do not copy verbatim).
6. Keep the entire message under 60 words.
7. End with one short encouraging phrase (under 8 words).

Return ONLY a JSON object with these exact keys:
{
  "title": "<short notification title, under 8 words>",
  "body":  "<the full message>",
  "cta":   "I have arrived"
}

No markdown. No explanation. Only valid JSON."""

async def writer_node(state: AgentState) -> Dict[str, Any]:
    from task_publish.task_agent.llm import llm_writer

    advice  = state["exercise_advice"]
    summary = state["health_summary"]

    # Writer receives only the distilled advice — not raw health data.
    # This keeps the token budget small and the prompt focused.
    user_prompt = f"""User name:       {summary["user_name"]}
Language:        {summary["language_pref"]}
Park:            {summary["selected_park_name"]} ({summary["selected_park_distance_m"]}m away)
Duration:        {advice["duration_min"]} minutes
Intensity:       {advice["intensity"]}
Personalized tip: {advice["personalized_tip"]}
Snack suggestion: {advice["snack_before_exercise"] or "none"}"""

    try:
        response = await llm_writer.acomplete(
            system=WRITER_SYSTEM_PROMPT,
            user=user_prompt,
        )
        task_content = _extract_json(response.text)
        
        # Validate required keys
        assert "title" in task_content and "body" in task_content
        return {"task_content": task_content}

    except Exception as e:
        logger.error(f"writer_node error: {str(e)}")
        # Fallback: construct minimal English copy from advice fields
        return {"task_content": {
            "title": f"Time for a walk, {summary['user_name']}!",
            "body":  (f"Head to {summary['selected_park_name']} for a "
                      f"{advice['duration_min']}-minute walk. "
                      f"{advice['personalized_tip']}"),
            "cta":   "I have arrived",
        }}
