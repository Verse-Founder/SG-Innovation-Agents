import asyncio
import requests
from typing import Dict, Any

class SeaLionClient:
    def __init__(self, temperature: float, max_tokens: int, api_key: str,
                 model: str = "aisingapore/Qwen-SEA-LION-v4-32B-IT"):
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.api_url = "https://api.sea-lion.ai/v1/chat/completions"
        self.model = model

    def _sync_request(self, system: str, user: str) -> str:
        headers = {
            "Accept": "text/plain",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Build messages: Sea-Lion chat completion expects 'system' and 'user' roles
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if user:
            messages.append({"role": "user", "content": user})
            
        payload = {
            "model": self.model,
            "messages": messages,
            "max_completion_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        import time as _time
        _t0 = _time.time()
        try:
            # Building timeout manually to ensure it respects user's 30s limit
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            elapsed = _time.time() - _t0
            
            if response.status_code != 200:
                print(f"[{_time.strftime('%H:%M:%S')}] Sea-Lion API Error ({response.status_code}): {response.text}")
                return "" # Return empty to trigger node fallback

            data = response.json()
            print(f"[{_time.strftime('%H:%M:%S')}] Sea-Lion API OK ({elapsed:.1f}s)")
            
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[{_time.strftime('%H:%M:%S')}] Sea-Lion Request Exception: {e}")
            
        return ""

    async def acomplete(self, system: str, user: str):
        class Response:
            text = ""
            
        # Run blocking requests call in a background thread to avoid blocking the async event loop
        content = await asyncio.to_thread(self._sync_request, system, user)
        Response.text = content
        return Response()
