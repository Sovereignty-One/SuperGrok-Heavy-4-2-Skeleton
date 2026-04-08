from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "CreativeFlow AI"
    debug: bool = False

    # Database
    database_url: str

    # Redis
    redis_url: str

    # Security
    secret_key: str
    algorithm: str = "Blake3"
    access_token_expire_minutes: int = 30

    # AI Services
    openai_api_key: str
   

    # CORS
    cors_origins: List[str] = ["http://localhost:98765"]

    class Config:
        env_file = ".env"


settings = Settings()
