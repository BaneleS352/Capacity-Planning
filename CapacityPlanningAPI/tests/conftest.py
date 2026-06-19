import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["DATABASE_CONNECTION_STRING"] = ""
os.environ["AUTH_MODE"] = "local"
os.environ["LOCAL_JWT_SECRET"] = "development-only-secret-change-me"  # noqa: S105

from app.core.config import get_settings  # noqa: E402
from app.infrastructure.database.base import Base  # noqa: E402
from app.infrastructure.database.session import get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Organization  # noqa: E402


@dataclass(slots=True)
class ApiContext:
    client: AsyncClient
    session: AsyncSession
    organization_id: UUID
    headers: dict[str, str]


def make_token(organization_id: UUID, roles: list[str], team_ids: list[UUID] | None = None) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": "test-user",
            "org_id": str(organization_id),
            "roles": roles,
            "team_ids": [str(value) for value in (team_ids or [])],
            "iat": now,
            "exp": now + timedelta(hours=1),
        },
        get_settings().local_jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


@pytest_asyncio.fixture
async def api_context() -> ApiContext:
    test_engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    session = factory()
    organization = Organization(name="Test Organization", slug="test", timezone="UTC")
    session.add(organization)
    await session.commit()
    await session.refresh(organization)

    async def override_session():  # type: ignore[no-untyped-def]
        yield session

    app.dependency_overrides[get_session] = override_session
    token = make_token(organization.id, ["system_admin"])
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield ApiContext(
            client=client,
            session=session,
            organization_id=organization.id,
            headers={"Authorization": f"Bearer {token}"},
        )
    app.dependency_overrides.clear()
    await session.close()
    await test_engine.dispose()
