import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_local_authentication() -> None:
    with pytest.raises(ValidationError, match="OIDC authentication"):
        Settings(
            environment="production",
            auth_mode="local",
            database_url="postgresql+asyncpg://example/database",
        )


def test_production_rejects_sqlite_even_with_oidc() -> None:
    with pytest.raises(ValidationError, match="SQLite"):
        Settings(
            environment="production",
            auth_mode="oidc",
            database_url="sqlite+aiosqlite:///unsafe.db",
            database_connection_string=None,
            oidc_issuer="https://issuer.example",
            oidc_audience="capacity-api",
            oidc_jwks_url="https://issuer.example/keys",
        )


def test_production_accepts_sql_server_connection_string() -> None:
    settings = Settings(
        environment="production",
        auth_mode="oidc",
        database_connection_string=(
            r"Server=(localdb)\\MSSQLLocalDB;Database=betteams;Trusted_Connection=True"
        ),
        oidc_issuer="https://issuer.example",
        oidc_audience="capacity-api",
        oidc_jwks_url="https://issuer.example/keys",
        jira_webhook_secret="j" * 32,
        payspace_webhook_secret="p" * 32,
    )

    assert settings.database_connection_string is not None
