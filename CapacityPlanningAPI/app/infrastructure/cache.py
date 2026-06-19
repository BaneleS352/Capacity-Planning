import json
from typing import Any

from redis.asyncio import Redis


class JsonCache:
    def __init__(self, redis: Redis, namespace: str = "capacity") -> None:
        self.redis = redis
        self.namespace = namespace

    def _key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    async def get(self, key: str) -> dict[str, Any] | None:
        value = await self.redis.get(self._key(key))
        if value is None:
            return None
        decoded = json.loads(value)
        return decoded if isinstance(decoded, dict) else None

    async def set(self, key: str, value: dict[str, Any], ttl_seconds: int = 300) -> None:
        await self.redis.set(
            self._key(key), json.dumps(value, default=str, separators=(",", ":")), ex=ttl_seconds
        )

    async def invalidate(self, key: str) -> None:
        await self.redis.delete(self._key(key))
