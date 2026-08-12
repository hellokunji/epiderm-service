from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Epiderm Clinic Service"
    PROJECT_DESCRIPTION: str = (
        "Clinic microservice for AI diagnosis of hair and skin problems."
    )
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "postgresql+psycopg2://epiderm:epiderm@localhost:5432/clinic"
    MONGODB_URL: str = "mongodb://epiderm:epiderm@localhost:27017/?authSource=epiderm"
    MONGODB_DB_NAME: str = "epiderm"

    S2S_API_KEY: str = "V8a3W7p9KsL4zR5bQ2xN1mC8TuSjXyP0"
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"

    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_VISION_MODEL: str = "gemma3:12b"
    OLLAMA_HOST: str = "http://localhost:11434"

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    CELERY_RESULT_EXPIRES: int = 86_400
    CELERY_DIAGNOSIS_WORKER_CONCURRENCY: int = 1

    @model_validator(mode="after")
    def set_celery_defaults(self) -> "Settings":
        if self.CELERY_BROKER_URL is None:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if self.CELERY_RESULT_BACKEND is None:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL
        return self


settings = Settings()
