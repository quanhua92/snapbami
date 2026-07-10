import pathlib

from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file(max_up: int = 4) -> str:
    d = pathlib.Path(__file__).resolve().parent
    for _ in range(max_up):
        candidate = d / ".env"
        if candidate.is_file():
            return str(candidate)
        d = d.parent
    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql://snapbami:changeme@localhost:5432/snapbami"
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

    STATIC_DIR: str = "../snapbami-web/dist"


settings = Settings()
