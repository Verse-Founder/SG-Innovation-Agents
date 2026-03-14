from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    sea_lion_api_key: str = "dummy_key"
    database_url: str = "sqlite:///./task_publish.db"
    redis_url: str = "redis://localhost:6379/0"

settings = Settings()
