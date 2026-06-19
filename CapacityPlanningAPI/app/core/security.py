import hashlib
import hmac
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import UUID

import httpx
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError, PyJWK
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.infrastructure.database.session import get_session
from app.models import Organization


class Role(StrEnum):
    DEVELOPMENT_MANAGER = "development_manager"
    SENIOR_MANAGER = "senior_manager"
    DELIVERY_LEAD = "delivery_lead"
    PRODUCT_OWNER = "product_owner"
    HR_ADMIN = "hr_admin"
    SYSTEM_ADMIN = "system_admin"
    EXECUTIVE = "executive"


ROLE_PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.DEVELOPMENT_MANAGER: frozenset(
        {"team:read", "employee:read", "leave:availability:read", "planning:write", "risk:write"}
    ),
    Role.SENIOR_MANAGER: frozenset(
        {
            "team:read",
            "employee:read",
            "leave:availability:read",
            "planning:write",
            "risk:write",
            "report:read",
        }
    ),
    Role.DELIVERY_LEAD: frozenset(
        {"team:read", "employee:read", "leave:availability:read", "planning:write", "risk:write"}
    ),
    Role.PRODUCT_OWNER: frozenset({"team:read", "leave:availability:read", "report:read"}),
    Role.HR_ADMIN: frozenset(
        {"employee:read", "employee:write", "leave:availability:read", "leave:reason:read"}
    ),
    Role.SYSTEM_ADMIN: frozenset({"*"}),
    Role.EXECUTIVE: frozenset({"report:read", "team:aggregate:read"}),
}


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    organization_id: UUID
    user_id: UUID | None
    email: str | None
    roles: frozenset[Role]
    team_ids: frozenset[UUID]
    explicit_permissions: frozenset[str] = frozenset()

    @property
    def permissions(self) -> frozenset[str]:
        values = set(self.explicit_permissions)
        for role in self.roles:
            values.update(ROLE_PERMISSIONS[role])
        return frozenset(values)

    def has_permission(self, permission: str) -> bool:
        permissions = self.permissions
        return "*" in permissions or permission in permissions

    def can_access_team(self, team_id: UUID) -> bool:
        return Role.SYSTEM_ADMIN in self.roles or team_id in self.team_ids


class JwksCache:
    def __init__(self) -> None:
        self._keys: dict[str, PyJWK] = {}
        self._expires_at = 0.0

    async def get_key(self, kid: str, settings: Settings) -> PyJWK:
        if time.monotonic() >= self._expires_at or kid not in self._keys:
            if settings.oidc_jwks_url is None:
                raise AuthenticationError("OIDC signing-key configuration is missing")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(settings.oidc_jwks_url)
                response.raise_for_status()
            payload = response.json()
            self._keys = {item["kid"]: PyJWK.from_dict(item) for item in payload.get("keys", [])}
            self._expires_at = time.monotonic() + settings.oidc_jwks_cache_seconds
        try:
            return self._keys[kid]
        except KeyError as exc:
            raise AuthenticationError("The token signing key is not recognized") from exc


jwks_cache = JwksCache()
bearer = HTTPBearer(auto_error=False)


def _principal_from_claims(claims: dict[str, Any]) -> Principal:
    try:
        raw_roles = claims.get("roles", [])
        roles = frozenset(Role(role) for role in raw_roles)
        organization_id = UUID(str(claims["org_id"]))
        team_ids = frozenset(UUID(str(value)) for value in claims.get("team_ids", []))
        user_id = UUID(str(claims["user_id"])) if claims.get("user_id") else None
    except (KeyError, TypeError, ValueError) as exc:
        raise AuthenticationError("Token authorization claims are invalid") from exc
    if not roles:
        raise AuthenticationError("The token contains no recognized application role")
    return Principal(
        subject=str(claims["sub"]),
        organization_id=organization_id,
        user_id=user_id,
        email=claims.get("email") or claims.get("preferred_username"),
        roles=roles,
        team_ids=team_ids,
        explicit_permissions=frozenset(claims.get("permissions", [])),
    )


async def verify_access_token(token: str, settings: Settings) -> Principal:
    try:
        if settings.auth_mode == "local":
            claims = jwt.decode(
                token,
                settings.local_jwt_secret.get_secret_value(),
                algorithms=["HS256"],
                options={"require": ["exp", "iat", "sub", "org_id", "roles"]},
            )
        else:
            header = jwt.get_unverified_header(token)
            key = await jwks_cache.get_key(str(header.get("kid", "")), settings)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=settings.oidc_algorithms,
                issuer=settings.oidc_issuer,
                audience=settings.oidc_audience,
                options={"require": ["exp", "iat", "sub"]},
            )
    except (InvalidTokenError, httpx.HTTPError) as exc:
        raise AuthenticationError("The access token is invalid or expired") from exc
    return _principal_from_claims(claims)


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> Principal:
    if credentials is None:
        if settings.auth_mode != "local" or settings.environment not in {"development", "test"}:
            raise AuthenticationError()
        organization_id = await session.scalar(
            select(Organization.id)
            .where(Organization.active.is_(True))
            .order_by(Organization.created_at, Organization.id)
            .limit(1)
        )
        if organization_id is None:
            raise AuthenticationError(
                "No active organization is available; run `python -m app.cli seed-demo` first"
            )
        return Principal(
            subject="local-system-admin",
            organization_id=organization_id,
            user_id=None,
            email=None,
            roles=frozenset({Role.SYSTEM_ADMIN}),
            team_ids=frozenset(),
        )
    if credentials.scheme.lower() != "bearer":
        raise AuthenticationError()
    return await verify_access_token(credentials.credentials, settings)


def require_permissions(*required: str):  # type: ignore[no-untyped-def]
    async def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        missing = [
            permission for permission in required if not principal.has_permission(permission)
        ]
        if missing:
            raise AuthorizationError(f"Missing required permission(s): {', '.join(missing)}")
        return principal

    return dependency


def require_team_access(principal: Principal, team_id: UUID) -> None:
    if not principal.can_access_team(team_id):
        raise AuthorizationError("You are not authorized for this team")


def validate_webhook_signature(
    *,
    body: bytes,
    timestamp: str,
    signature: str,
    secret: str,
    tolerance_seconds: int,
) -> None:
    try:
        sent_at = int(timestamp)
    except ValueError as exc:
        raise AuthenticationError("Webhook timestamp is invalid") from exc
    if abs(int(time.time()) - sent_at) > tolerance_seconds:
        raise AuthenticationError("Webhook timestamp is outside the allowed replay window")
    signed = timestamp.encode() + b"." + body
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    supplied = signature.removeprefix("sha256=")
    if not hmac.compare_digest(expected, supplied):
        raise AuthenticationError("Webhook signature is invalid")
