from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "EmoraTest API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://localhost:5432/emoratest"
    REDIS_URL: str = "redis://localhost:6379/0"

    CORS_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8000",  # SDK test page
    "http://127.0.0.1:8000",   # Alternative localhost
    "http://127.0.0.1:3001",   # Alternative localhost for demo store
    "http://localhost:5500",   # Common for local HTML files
    "*"  # Allow all for development (remove in production)
]

    # JWT settings
    JWT_SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
