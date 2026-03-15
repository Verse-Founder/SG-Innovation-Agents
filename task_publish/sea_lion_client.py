import asyncio
import requests
from typing import Dict, Any

class SeaLionClient:
    def __init__(self, temperature: float, max_tokens: int, api_key: str):
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.api_url = "https://api.sea-lion.ai/v1/chat/completions"
        self.model = "aisingapore/Gemma-SEA-LION-v4-27B-IT"

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
        
        response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"Sea-Lion API Error: {response.text}")
            return "{}"

        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
            
        return "{}"

    async def acomplete(self, system: str, user: str):
        class Response:
            text = ""
            
        # Run blocking requests call in a background thread to avoid blocking the async event loop
        content = await asyncio.to_thread(self._sync_request, system, user)
        Response.text = content
        return Response()
