"""Rate limiting for bot commands and API calls."""

from datetime import datetime, timedelta
from typing import Optional

import redis.asyncio as redis


class RateLimiter:
    """Redis-based rate limiter."""

    def __init__(
        self,
        redis_url: str,
        max_requests: int = 10,
        window_seconds: int = 60,
    ):
        """Initialize rate limiter."""
        self.redis_url = redis_url
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        self._client = await redis.from_url(self.redis_url, encoding="utf-8")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()

    async def check_rate_limit(self, user_id: int, action: str) -> tuple[bool, Optional[int]]:
        """Check if user has exceeded rate limit.

        Returns:
            (is_allowed, retry_after_seconds)
        """
        if not self._client:
            raise RuntimeError("Redis client not connected")

        key = f"tmkt:ratelimit:{action}:{user_id}"
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        # Remove old entries outside window
        await self._client.zremrangebyscore(key, 0, window_start.timestamp())

        # Count requests in current window
        count = await self._client.zcard(key)

        if count >= self.max_requests:
            # Get oldest request in window to calculate retry_after
            oldest = await self._client.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_time = datetime.fromtimestamp(oldest[0][1])
                retry_after = int((oldest_time + timedelta(seconds=self.window_seconds) - now).total_seconds())
                return False, retry_after
            return False, self.window_seconds

        # Add current request
        await self._client.zadd(key, {str(now.timestamp()): now.timestamp()})
        await self._client.expire(key, self.window_seconds)

        return True, None

    async def reset_limit(self, user_id: int, action: str) -> None:
        """Reset rate limit for user action."""
        if not self._client:
            raise RuntimeError("Redis client not connected")

        key = f"tmkt:ratelimit:{action}:{user_id}"
        await self._client.delete(key)
