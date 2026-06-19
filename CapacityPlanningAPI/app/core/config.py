from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Capacity Planning API"
    environment: Literal["development", "test", "staging", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./capacity_planning.db"
    database_connection_string: str | None = None
    database_odbc_driver: str = "ODBC Driver 18 for SQL Server"
    database_echo: bool = False

    auth_mode: Literal["oidc", "local"] = "local"
    local_jwt_secret: SecretStr = SecretStr("development-only-secret-change-me")
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_jwks_url: str | None = None
    oidc_algorithms: list[str] = Field(default_factory=lambda: ["RS256"])
    oidc_jwks_cache_seconds: int = 3600

    jira_webhook_secret: SecretStr = SecretStr("development-jira-secret")
    payspace_webhook_secret: SecretStr = SecretStr("development-payspace-secret")
    webhook_tolerance_seconds: int = 300

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    allowed_origins: list[str] = Field(default_factory=list)
    log_level: str = "INFO"
    max_page_size: int = 200
    default_page_size: int = 50

    @model_validator(mode="after")
    def validate_security_posture(self) -> Self:
        if self.auth_mode == "oidc":
            missing = [
                name
                for name, value in (
                    ("OIDC_ISSUER", self.oidc_issuer),
                    ("OIDC_AUDIENCE", self.oidc_audience),
                    ("OIDC_JWKS_URL", self.oidc_jwks_url),
                )
                if not value
            ]
            if missing:
                raise ValueError(f"OIDC configuration is incomplete: {', '.join(missing)}")

        if self.environment in {"staging", "production"}:
            if self.auth_mode != "oidc":
                raise ValueError("OIDC authentication is required outside development/test")
            if not self.database_connection_string and self.database_url.startswith("sqlite"):
                raise ValueError("SQLite is not allowed outside development/test")
            secrets = (
                self.jira_webhook_secret.get_secret_value(),
                self.payspace_webhook_secret.get_secret_value(),
            )
            if any("development" in secret or len(secret) < 32 for secret in secrets):
                raise ValueError("Strong webhook secrets are required outside development/test")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
