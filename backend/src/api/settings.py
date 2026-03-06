from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openweather_api_key: str = Field(
        ...,
        alias="OPENWEATHER_API_KEY",
        description="OpenWeatherMap API key used for all upstream requests.",
    )
    weather_cache_ttl_seconds: int = Field(
        600,
        alias="WEATHER_CACHE_TTL_SECONDS",
        description="TTL (seconds) for in-memory caching of weather responses.",
        ge=0,
    )


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Return the application Settings instance.

    Returns:
        Settings: loaded settings (from env, optionally .env).
    """
    return Settings()
