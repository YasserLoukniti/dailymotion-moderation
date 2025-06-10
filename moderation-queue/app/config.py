from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_host: str = "mysql"
    database_port: int = 3306
    database_name: str = "moderation"
    database_user: str = "moderation_user"
    database_password: str = "moderation_pass"

    # Database connection pool settings
    db_min_pool_size: int = 5
    db_max_pool_size: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
