"""Rate limiter for scan tasks using Redis."""
import time
from typing import Optional

import redis

from shared.config import settings


class RateLimiter:
    """Token bucket rate limiter using Redis."""

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        key_prefix: str = "ratelimit",
    ):
        self.redis = redis_client or redis.from_url(settings.redis_url)
        self.key_prefix = key_prefix

    def _get_key(self, identifier: str) -> str:
        return f"{self.key_prefix}:{identifier}"

    def is_allowed(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """Check if request is allowed under rate limit."""
        key = self._get_key(identifier)
        current_time = int(time.time())
        window_start = current_time - window_seconds

        pipe = self.redis.pipeline()
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        # Count current entries
        pipe.zcard(key)
        # Add new entry
        pipe.zadd(key, {str(current_time): current_time})
        # Set expiry
        pipe.expire(key, window_seconds + 1)
        results = pipe.execute()

        current_count = results[1]
        return current_count < max_requests

    def wait_if_needed(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
        max_wait: float = 10.0,
    ) -> bool:
        """Wait until rate limit allows, or timeout."""
        start = time.time()
        while time.time() - start < max_wait:
            if self.is_allowed(identifier, max_requests, window_seconds):
                return True
            time.sleep(0.1)
        return False

    def get_remaining(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
    ) -> int:
        """Get remaining requests in current window."""
        key = self._get_key(identifier)
        current_time = int(time.time())
        window_start = current_time - window_seconds

        self.redis.zremrangebyscore(key, 0, window_start)
        current_count = self.redis.zcard(key)
        return max(0, max_requests - current_count)


# Global rate limiter instance
_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter."""
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()
    return _limiter
