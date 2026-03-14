import asyncio
from src.vision_agent.agent import VisionAgent
from src.vision_agent.llm.gemini import GeminiVLM

async def test_vision():
    try:
        agent = VisionAgent(vlm=GeminiVLM())
        # Provide a dummy image to test integration syntax
        # result = agent.analyze("meal_photo.jpg")
        print("VisionAgent imported successfully with GeminiVLM!")
    except Exception as e:
        print(f"Vision integration mock setup error: {e}")

if __name__ == "__main__":
    asyncio.run(test_vision())
