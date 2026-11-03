import json

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "OptiGuide"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./local_dev.db"
    DB_ECHO: bool = False

    # Security & JWT
    JWT_SECRET_KEY: str = "dev-insecure-secret-key-change-in-production-optiguide-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_GRACE_PERIOD_SECONDS: int = 10
    JWT_ISSUER: str = "optiguide-api"
    JWT_AUDIENCE: str = "optiguide-client"
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 128

    # Rate Limiting & Proxy Configuration
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 10
    REGISTER_RATE_LIMIT_PER_MINUTE: int = 5
    TRUST_FORWARDED_FOR: bool = False
    TRUSTED_PROXIES: list[str] | str = ["127.0.0.1", "::1"]

    # CORS
    CORS_ORIGINS: list[str] | str = [
        "http://localhost:3000",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:19006",
    ]

    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", "TRUSTED_PROXIES", mode="before")
    @classmethod
    def assemble_string_list(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.APP_ENV == "production":
            insecure_keys = {
                "dev-insecure-secret-key-change-in-production-optiguide-2026",
                "secret",
                "changeme",
            }
            if self.JWT_SECRET_KEY in insecure_keys or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: "
                    "JWT_SECRET_KEY must be a cryptographically secure string "
                    "(minimum 32 characters) in production environment."
                )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
