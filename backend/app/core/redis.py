"""
Redis client and connection management for PustakHub.

Used in Phase 3 exclusively for temporary registration and OTP state.

SECURITY:
  - Redis connection URL is read from environment settings.
  - Credentials or connection strings are never logged.
"""

from typing import Optional

import redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """
    Get or initialize the shared Redis client instance.

    Uses `decode_responses=True` so all returned values are strings.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            settings.REDIS_URL or "redis://localhost:6379/0",
            decode_responses=True,
            protocol=2,
            socket_timeout=3.0,
            socket_connect_timeout=3.0,
        )
    return _redis_client


def check_redis_connection() -> bool:
    """
    Check if the Redis server is reachable.

    Returns:
        True if Redis responds to ping, False otherwise.
    """
    try:
        client = get_redis_client()
        return bool(client.ping())
    except (RedisError, ConnectionError, Exception) as exc:
        logger.warning("Redis connectivity check failed: %s", type(exc).__name__)
        return False
