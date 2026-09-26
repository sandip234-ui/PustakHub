"""
Rate Limiting Middleware for FastAPI.

Intercepts requests and enforces category-specific Redis sliding window limits.
Attaches standard rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining,
X-RateLimit-Reset, Retry-After) to HTTP responses.
"""

from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import get_logger
from app.core.ratelimit import rate_limiter, resolve_rate_limit_policy

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces Redis-backed rate limiting per IP and route category.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Preflight requests (OPTIONS) are handled by CORS middleware and should not count against rate limits
        if request.method.upper() == "OPTIONS" or not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        path = request.url.path
        method = request.method

        category, limit, window_seconds, fail_closed = resolve_rate_limit_policy(path, method)

        if category == "exempt":
            return await call_next(request)

        # Resolve client identifier (from AuditContextMiddleware or request headers)
        client_ip = getattr(request.state, "client_ip", None)
        if not client_ip:
            client_ip = request.headers.get("X-Forwarded-For")
            if client_ip:
                client_ip = client_ip.split(",")[0].strip()
            elif request.client:
                client_ip = request.client.host
            else:
                client_ip = "127.0.0.1"

        result = rate_limiter.check_rate_limit(
            identifier=client_ip,
            category=category,
            limit=limit,
            window_seconds=window_seconds,
            fail_closed=fail_closed,
        )

        if not result.allowed:
            if result.error == "redis_unavailable_fail_closed":
                logger.warning(
                    "Blocked request to security-critical endpoint %s %s from %s due to Redis unavailability (fail-closed)",
                    method,
                    path,
                    client_ip,
                )
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "service_unavailable",
                        "message": "Authentication service temporarily unavailable. Please try again shortly.",
                        "detail": None,
                    },
                    headers={
                        "Retry-After": str(result.retry_after),
                    },
                )

            logger.warning(
                "Rate limit exceeded for category=%s, client=%s on %s %s",
                category,
                client_ip,
                method,
                path,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "detail": None,
                },
                headers={
                    "Retry-After": str(result.retry_after),
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(result.reset_epoch),
                },
            )

        response = await call_next(request)

        # Attach rate-limit metadata headers to successful/processed response
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_epoch)

        return response
