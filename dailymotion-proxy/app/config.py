from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    redis_url: str = "redis://redis:6379/0"
    dailymotion_api_base_url: str = "https://api.dailymotion.com"
    cache_ttl: int = 300

    # The reference video used for all proxy requests (as per test spec)
    reference_video_id: str = "xa0apeu"

    # HTTP client settings
    http_timeout: float = 10.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
