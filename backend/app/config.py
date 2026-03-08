from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_env: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://studyforge:studyforge@localhost:5432/studyforge"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"

    # S3
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "studyforge-docs"
    s3_region: str = "us-east-1"

    # OpenAI
    openai_api_key: str = ""

    # Anthropic
    anthropic_api_key: str = ""

    # Upload limits
    max_file_size_mb: int = 25
    max_page_count: int = 200
    daily_chat_limit: int = 50

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def sync_database_url(self) -> str:
        """Sync URL for Alembic migrations."""
        return self.database_url.replace("+asyncpg", "+psycopg2")


settings = Settings()
