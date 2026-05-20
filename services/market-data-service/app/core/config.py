from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "market-data-service"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/quantos"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/1"

    # Auth — must match api-gateway JWT_SECRET
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Data providers (gated — set to false unless key provided)
    POLYGON_API_KEY: str = ""
    ALPHAVANTAGE_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    NEWSAPI_KEY: str = ""
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    ENABLE_POLYGON: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


settings = Settings()
