import os

# Dummy client for LLM, in a real env it would be the actual SDK
class SeaLionClient:
    def __init__(self, temperature: float, max_tokens: int, api_key: str):
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key
    
    async def acomplete(self, system: str, user: str):
        class Response:
            text = "{}"
        return Response()
