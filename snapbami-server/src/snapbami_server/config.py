from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/snapbami"
    REDIS_URL: str = "redis://localhost:6379/0"

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    FIREBASE_SA_PATH: str = "/etc/snapbami/firebase-service-account.json"

    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = "snapbami"
    S3_REGION: str = "us-east-1"

    # Where the built SPA lives. In dev: ../snapbami-web/dist
    # In Docker: /app/static (copied in Dockerfile). Override via env.
    STATIC_DIR: str = "../snapbami-web/dist"


settings = Settings()
