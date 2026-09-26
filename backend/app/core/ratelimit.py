"""
Redis-backed sliding window rate limiter for PustakHub.

Implements an atomic sliding window counter using Redis sorted sets (ZSET)
and Lua scripting to ensure deterministic, process-safe, bounded memory rate limiting.

Key Strategy:
  - Format: `ratelimit:<category>:<identifier>`
  - No passwords, JWTs, tokens, or plaintext secrets in Redis keys.
  - Normalized categories prevent key-space explosion.
"""

from dataclasses import dataclass
import math
import time
from typing import Optional, Tuple
import uuid

from redis.exceptions import RedisError

from app.core.config import settings
from app.core.logging import get_logger
from app.core.redis import get_redis_client

logger = get_logger(__name__)


# Atomic Lua script for sliding window rate limiting via Redis ZSET
# ARGV[1] = current timestamp (seconds float)
# ARGV[2] = window duration (seconds int)
# ARGV[3] = max requests limit (int)
# ARGV[4] = unique member identifier
SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_limit = tonumber(ARGV[3])
local member_id = ARGV[4]
local clear_before = now - window

-- 1. Evict expired entries outside the sliding window
redis.call('ZREMRANGEBYSCORE', key, '-inf', clear_before)

-- 2. Count active entries within current window
local current_count = redis.call('ZCARD', key)

if current_count < max_limit then
    -- 3. Add current request with timestamp as score
    redis.call('ZADD', key, now, member_id)
    -- Set TTL to window + 1 second buffer
    redis.call('EXPIRE', key, math.ceil(window) + 1)
    local remaining = max_limit - current_count - 1
    return {1, remaining, 0}
else
    -- Exceeded limit: calculate retry_after from the oldest entry in window
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = math.ceil(window)
    if oldest and #oldest >= 2 then
        local oldest_time = tonumber(oldest[2])
        retry_after = math.max(1, math.ceil(oldest_time + window - now))
    end
    return {0, 0, retry_after}
end
"""


@dataclass(frozen=True)
class RateLimitResult:
    """Encapsulates the result of a rate limit evaluation."""

    allowed: bool
    remaining: int
    limit: int
    retry_after: int
    reset_epoch: int
    category: str
    error: Optional[str] = None


class RateLimiter:
    """
    Central Redis-backed sliding window rate limiter.
    """

    def __init__(self) -> None:
        self._lua_script = None

    def _get_script(self, client):
        if self._lua_script is None:
            self._lua_script = client.register_script(SLIDING_WINDOW_LUA)
        return self._lua_script

    def check_rate_limit(
        self,
        identifier: str,
        category: str,
        limit: int,
        window_seconds: int,
        fail_closed: bool = False,
    ) -> RateLimitResult:
        """
        Evaluate rate limit for a given identifier within a category.

        Args:
            identifier: Sanitized client identifier (e.g. IP address or safe user ID).
            category: Normalized endpoint category (e.g. 'auth_login').
            limit: Maximum requests allowed in the window.
            window_seconds: Window duration in seconds.
            fail_closed: If True, block requests when Redis is unavailable.

        Returns:
            RateLimitResult containing allowed status, remaining quota, retry_after, and reset time.
        """
        now = time.time()
        key = f"ratelimit:{category}:{identifier}"
        member_id = f"{now}-{uuid.uuid4().hex[:8]}"

        try:
            client = get_redis_client()
            script = self._get_script(client)
            result = script(keys=[key], args=[now, window_seconds, limit, member_id], client=client)
            
            allowed = bool(result[0])
            remaining = int(result[1])
            retry_after = int(result[2])
            reset_epoch = int(now + (retry_after if not allowed else window_seconds))

            return RateLimitResult(
                allowed=allowed,
                remaining=remaining,
                limit=limit,
                retry_after=retry_after,
                reset_epoch=reset_epoch,
                category=category,
            )
        except (RedisError, ConnectionError, Exception) as exc:
            logger.error(
                "Redis rate limiter error for category=%s (fail_closed=%s): %s",
                category,
                fail_closed,
                type(exc).__name__,
            )
            if fail_closed:
                # Security-critical endpoint: fail closed to block potential brute force
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    limit=limit,
                    retry_after=window_seconds,
                    reset_epoch=int(now + window_seconds),
                    category=category,
                    error="redis_unavailable_fail_closed",
                )
            else:
                # Non-critical endpoint: fail open to preserve user experience
                return RateLimitResult(
                    allowed=True,
                    remaining=limit,
                    limit=limit,
                    retry_after=0,
                    reset_epoch=int(now + window_seconds),
                    category=category,
                    error="redis_unavailable_fail_open",
                )


rate_limiter = RateLimiter()


def resolve_rate_limit_policy(path: str, method: str) -> Tuple[str, int, int, bool]:
    """
    Resolve the route path and HTTP method into rate limit policy parameters:
    (category, limit, window_seconds, fail_closed).

    Returns category 'exempt' for health and documentation routes.
    """
    normalized_path = path.rstrip("/")
    if not normalized_path:
        normalized_path = "/"

    # Exempt: health, root, and documentation endpoints
    if normalized_path in (
        "/",
        "/api/health",
        "/health",
        "/ready",
        "/live",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
    ):
        return "exempt", 0, 0, False

    method_upper = method.upper()

    # 1. Auth: Login (Strict)
    if normalized_path == "/api/v1/auth/login" and method_upper == "POST":
        return (
            "auth_login",
            settings.RATE_LIMIT_AUTH_REQUESTS,
            settings.RATE_LIMIT_AUTH_WINDOW_SECONDS,
            settings.RATE_LIMIT_FAIL_CLOSED_AUTH,
        )

    # 2. Auth: Registration & OTP Verification (Strict)
    if normalized_path in ("/api/v1/auth/register", "/api/v1/auth/verify-otp") and method_upper == "POST":
        return (
            "auth_register",
            settings.RATE_LIMIT_REGISTER_REQUESTS,
            settings.RATE_LIMIT_REGISTER_WINDOW_SECONDS,
            settings.RATE_LIMIT_FAIL_CLOSED_AUTH,
        )

    # 3. Auth: Password Reset & Forgot Password (Strict)
    if normalized_path in ("/api/v1/auth/forgot-password", "/api/v1/auth/reset-password") and method_upper == "POST":
        return (
            "auth_password_reset",
            settings.RATE_LIMIT_PASSWORD_RESET_REQUESTS,
            settings.RATE_LIMIT_PASSWORD_RESET_WINDOW_SECONDS,
            settings.RATE_LIMIT_FAIL_CLOSED_AUTH,
        )

    # 4. Auth: MFA Verification, Enrollment, Disablement (Strict)
    if normalized_path.startswith("/api/v1/auth/mfa") and method_upper == "POST":
        return (
            "auth_mfa",
            settings.RATE_LIMIT_MFA_REQUESTS,
            settings.RATE_LIMIT_MFA_WINDOW_SECONDS,
            settings.RATE_LIMIT_FAIL_CLOSED_AUTH,
        )

    # 5. General API (Permissive)
    if normalized_path.startswith("/api/"):
        return (
            "api_general",
            settings.RATE_LIMIT_API_REQUESTS,
            settings.RATE_LIMIT_API_WINDOW_SECONDS,
            False,  # Fail open for general API operations if Redis is down
        )

    return "exempt", 0, 0, False
