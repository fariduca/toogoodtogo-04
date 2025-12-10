"""Redis-based distributed locks for inventory reservation."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import UUID

import redis.asyncio as redis


class RedisLockHelper:
    """Helper for Redis-based distributed locking."""

    def __init__(self, redis_url: str, ttl_seconds: int = 5):
        """Initialize Redis lock helper."""
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        self._client = await redis.from_url(self.redis_url, encoding="utf-8")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()

    @asynccontextmanager
    async def acquire_offer_lock(
        self, offer_id: UUID
    ) -> AsyncGenerator[bool, None]:
        """Acquire exclusive lock on offer for purchase operations."""
        if not self._client:
            raise RuntimeError("Redis client not connected")

        lock_key = f"tmkt:lock:offer:{offer_id}"
        acquired = False

        try:
            # Try to acquire lock with NX (set if not exists)
            acquired = await self._client.set(
                lock_key, "1", ex=self.ttl_seconds, nx=True
            )
            yield bool(acquired)
        finally:
            if acquired:
                await self._client.delete(lock_key)

    async def is_locked(self, offer_id: UUID) -> bool:
        """Check if offer is currently locked."""
        if not self._client:
            raise RuntimeError("Redis client not connected")

        lock_key = f"tmkt:lock:offer:{offer_id}"
        return bool(await self._client.exists(lock_key))
