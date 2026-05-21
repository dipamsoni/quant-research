from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "portfolio-service"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/quantos"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/2"

    # Auth — must match api-gateway JWT_SECRET
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Internal service URLs
    MARKET_DATA_SERVICE_URL: str = "http://localhost:8001"

    # Risk metrics
    RISK_FREE_RATE: float = 0.065  # Indian 10-year G-sec yield; override via env var
    INTERNAL_TOKEN_EXP_SECONDS: int = 300

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


settings = Settings()
