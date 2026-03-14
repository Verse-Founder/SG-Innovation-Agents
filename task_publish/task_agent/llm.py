from task_publish.sea_lion_client import SeaLionClient
from task_publish.config import settings

# Clinical reasoning: low temperature for conservative, deterministic output
llm_advisor = SeaLionClient(
    temperature=0.1,
    max_tokens=512,
    api_key=settings.sea_lion_api_key,
)

# Copywriting: higher temperature for natural, warm tone
llm_writer = SeaLionClient(
    temperature=0.6,
    max_tokens=256,
    api_key=settings.sea_lion_api_key,
)
