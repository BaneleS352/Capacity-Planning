import argparse
import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import jwt
from sqlalchemy import select

from app.core.config import get_settings
from app.infrastructure.database.session import AsyncSessionFactory, engine
from app.models import CapacityProfile, Organization, RiskThreshold


def print_local_credentials(organization_id: UUID) -> None:
    settings = get_settings()
    if settings.auth_mode != "local":
        return
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": "local-system-admin",
            "org_id": str(organization_id),
            "roles": ["system_admin"],
            "iat": now,
            "exp": now + timedelta(hours=8),
        },
        settings.local_jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    print(f"Organization ID: {organization_id}")
    print(f"Development bearer token: {token}")


async def seed(slug: str, name: str, *, show_credentials: bool = True) -> UUID:
    async with AsyncSessionFactory() as session:
        organization = await session.scalar(select(Organization).where(Organization.slug == slug))
        if organization is None:
            organization = Organization(name=name, slug=slug, timezone="UTC")
            session.add(organization)
            await session.flush()
        profile_defaults = {
            "Backend Developer": (Decimal("10"), Decimal("5"), Decimal("5"), Decimal("10")),
            "Frontend Developer": (Decimal("10"), Decimal("5"), Decimal("5"), Decimal("10")),
            "QA Engineer": (Decimal("15"), Decimal("5"), Decimal("5"), Decimal("10")),
            "Tech Lead": (Decimal("20"), Decimal("10"), Decimal("10"), Decimal("10")),
            "DevOps Engineer": (Decimal("15"), Decimal("15"), Decimal("5"), Decimal("15")),
        }
        for role, buffers in profile_defaults.items():
            exists = await session.scalar(
                select(CapacityProfile).where(
                    CapacityProfile.organization_id == organization.id,
                    CapacityProfile.role_name == role,
                )
            )
            if exists is None:
                session.add(
                    CapacityProfile(
                        organization_id=organization.id,
                        role_name=role,
                        meeting_buffer_percent=buffers[0],
                        support_buffer_percent=buffers[1],
                        review_buffer_percent=buffers[2],
                        unplanned_buffer_percent=buffers[3],
                    )
                )
        threshold_defaults = [
            ("UTILIZATION", Decimal("95"), Decimal("110"), {"under": "70"}),
            ("SCOPE_CREEP", None, Decimal("20"), {}),
            ("CRITICAL_ROLE_UNAVAILABLE", None, Decimal("25"), {}),
            ("LOW_COMPLETION_PROBABILITY", None, Decimal("30"), {}),
            ("BLOCKED_WORK", None, None, {"days": 2}),
            ("DATA_STALENESS", None, None, {"hours": 8}),
        ]
        for risk_type, warning, critical, configuration in threshold_defaults:
            exists = await session.scalar(
                select(RiskThreshold).where(
                    RiskThreshold.organization_id == organization.id,
                    RiskThreshold.team_id.is_(None),
                    RiskThreshold.risk_type == risk_type,
                )
            )
            if exists is None:
                session.add(
                    RiskThreshold(
                        organization_id=organization.id,
                        risk_type=risk_type,
                        warning_value=warning,
                        critical_value=critical,
                        configuration=configuration,
                    )
                )
        await session.commit()
    if show_credentials:
        print_local_credentials(organization.id)
    return organization.id


async def seed_demo_workspace(slug: str, name: str) -> UUID:
    from app.demo_data import seed_demo

    organization_id = await seed(slug, name, show_credentials=False)
    await seed_demo(organization_id)
    return organization_id


async def run_command(command: str, slug: str, name: str) -> None:
    try:
        if command == "seed":
            await seed(slug, name)
        else:
            organization_id = await seed_demo_workspace(slug, name)
            print_local_credentials(organization_id)
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Capacity Planning administrative CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    seed_parser = subparsers.add_parser("seed", help="Seed organization defaults")
    seed_parser.add_argument("--slug", required=True)
    seed_parser.add_argument("--name", required=True)
    demo_parser = subparsers.add_parser("seed-demo", help="Seed a realistic demo workspace")
    demo_parser.add_argument("--slug", default="demo")
    demo_parser.add_argument("--name", default="Demo Engineering Organization")
    args = parser.parse_args()
    asyncio.run(run_command(args.command, args.slug, args.name))


if __name__ == "__main__":
    main()
