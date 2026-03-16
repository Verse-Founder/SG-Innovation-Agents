from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the .env file relative to THIS config.py file, not the CWD
_ENV_FILE = Path(__file__).parent / ".env"

class Settings(BaseSettings):
    sea_lion_api_key: str = "dummy_key"
    google_maps_api_key: str = "dummy_key"
    gemini_api_key: str = "dummy_key"
    database_url: str = "sqlite:///./task_publish.db"
    redis_url: str = "redis://localhost:6379/0"
    
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
