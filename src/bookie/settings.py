from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Triple-slash = local Unix socket + peer auth (no password needed).
    # Override in .env for remote/production:
    #   DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
    database_url: str = "postgresql+asyncpg:///bookie"
    debug: bool = False


settings = Settings()
