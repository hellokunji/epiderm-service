from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Epiderm Clinic Service"
    PROJECT_DESCRIPTION: str = (
        "Clinic microservice for AI diagnosis of hair and skin problems."
    )
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./test.db"

    S2S_API_KEY: str = "V8a3W7p9KsL4zR5bQ2xN1mC8TuSjXyP0"
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"

    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_VISION_MODEL: str = "gemma3:12b"
    OLLAMA_HOST: str = "http://localhost:11434"

    class Config:
        env_file = ".env"


settings = Settings()
