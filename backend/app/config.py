from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    mongodb_url: str
    mongodb_database: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200
    upload_dir: str = "./storage/videos"
    chroma_persist_dir: str = "./storage/chroma_db"
    gemini_api_keys: str  # Comma-separated API keys for rotation

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
