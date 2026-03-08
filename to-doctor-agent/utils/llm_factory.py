"""
utils/llm_factory.py
SEA-LION LLM 封装 — 与 task-agent 一致
"""
import logging
import requests
from config import settings

logger = logging.getLogger(__name__)


def call_sealion(
    prompt: str,
    model: str = None,
    max_tokens: int = 1500,
    temperature: float = 0.3,
) -> str:
    """调用 SEA-LION API（推理或对话模型）"""
    model = model or settings.SEALION_REASONING_MODEL
    headers = {
        "Authorization": f"Bearer {settings.SEALION_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        resp = requests.post(
            f"{settings.SEALION_BASE_URL}/chat/completions",
            json=payload, headers=headers, timeout=settings.REPORT_GENERATION_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning(f"[LLM] SEA-LION 调用失败: {e}, 尝试 Cloudflare 备用")
        try:
            resp = requests.post(
                f"{settings.CF_BASE_URL}/chat/completions",
                json=payload, headers=headers, timeout=settings.REPORT_GENERATION_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e2:
            logger.error(f"[LLM] Cloudflare 也失败: {e2}")
            return ""
