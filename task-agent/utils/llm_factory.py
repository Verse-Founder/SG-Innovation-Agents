"""
utils/llm_factory.py
SEA-LION API 调用封装
对话模型：aisingapore/Qwen-SEA-LION-v4-32B-IT
推理模型：aisingapore/Llama-SEA-LION-v3.5-70B-R
备用：Cloudflare Gemma-SEA-LION-v4
"""
import requests
from config.settings import (
    SEALION_BASE_URL, SEALION_API_KEY,
    SEALION_INSTRUCT_MODEL, SEALION_REASONING_MODEL,
    CF_BASE_URL,
)


def call_sealion(system_prompt: str, user_message: str, reasoning: bool = False) -> str:
    """单轮调用"""
    return call_sealion_with_history(
        system_prompt,
        [{"role": "user", "content": user_message}],
        reasoning=reasoning,
    )


def call_sealion_with_history(
    system_prompt: str,
    messages: list,
    reasoning: bool = False,
) -> str:
    """
    带对话历史的调用
    reasoning=True 使用推理模型（用于医学分析），否则使用对话模型（用于温暖话术生成）
    限流时自动切换 Cloudflare Gemma 备用
    """
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    model = SEALION_REASONING_MODEL if reasoning else SEALION_INSTRUCT_MODEL

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SEALION_API_KEY}",
    }
    payload = {"model": model, "messages": full_messages}

    try:
        resp = requests.post(
            f"{SEALION_BASE_URL}/chat/completions",
            json=payload, headers=headers, timeout=60,
        )
        if resp.status_code == 429:
            raise Exception("429 限流")
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

        # 推理模型可能有 <think>...</think> 标签，去除
        if "</think>" in content:
            content = content.split("</think>")[-1].strip()

        print(f"[SEA-LION] {'推理' if reasoning else '对话'}模型调用成功")
        return content

    except Exception as e:
        print(f"[SEA-LION] {e}，切换到 Cloudflare Gemma 备用")
        return _call_cloudflare_fallback(system_prompt, messages)


def _call_cloudflare_fallback(system_prompt: str, messages: list) -> str:
    """Cloudflare Gemma-SEA-LION 备用"""
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    headers = {"Content-Type": "application/json"}
    payload = {"messages": full_messages}

    try:
        resp = requests.post(
            f"{CF_BASE_URL}/chat",
            json=payload, headers=headers, timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        print(f"[Cloudflare Gemma] 备用调用成功")
        return content
    except Exception as e:
        print(f"[Cloudflare Gemma] 也失败了：{e}")
        return "抱歉，服务暂时不可用，请稍后再试。"
