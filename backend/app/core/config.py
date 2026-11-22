from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://aml:aml_password@localhost:5432/aml_platform"
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
