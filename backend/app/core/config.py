from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    secret_key: str = Field(alias="SECRET_KEY")
    algorithm: str = Field(alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        populate_by_name=True,
        case_sensitive=True,
    )


settings = Settings()


def get_cors_origins() -> list[str]:
    return [
        origin.strip()
        for origin in settings.cors_origins.split(",")
        if origin.strip()
    ]