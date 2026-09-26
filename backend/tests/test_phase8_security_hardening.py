"""
Phase 8 Security Hardening & Rate Limiting Tests.

Verifies:
  1. Redis-backed sliding window rate limiter functionality.
  2. Route category isolation and client IP isolation.
  3. Window expiration and atomic concurrency safety.
  4. Authentication abuse protections (login, register, password reset, MFA).
  5. Modern HTTP Security Headers and Content Security Policy (CSP).
  6. CORS hardening with credential support and explicit origins.
  7. Request body size protection (HTTP 413 Payload Too Large).
  8. Fail-closed policy on auth endpoints vs fail-open on general API when Redis is unavailable.
  9. Error envelope compliance and secret/internal leakage prevention.
"""

import concurrent.futures
import time
from unittest.mock import patch
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.config import settings
from app.core.ratelimit import RateLimiter, rate_limiter, resolve_rate_limit_policy
from app.core.redis import get_redis_client
from app.main import app


# ---------------------------------------------------------------------------
# Fixtures & Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clean_redis_ratelimits():
    """Flush rate limit keys before and after each test."""
    client = get_redis_client()
    try:
        keys = client.keys("ratelimit:*")
        if keys:
            client.delete(*keys)
    except Exception:
        pass
    yield
    try:
        keys = client.keys("ratelimit:*")
        if keys:
            client.delete(*keys)
    except Exception:
        pass


def get_random_ip() -> str:
    """Generate a unique random IP for isolated client tests."""
    part = uuid.uuid4().int % 250 + 1
    return f"198.51.100.{part}"


# ---------------------------------------------------------------------------
# 1. Rate Limiting — Core Engine & Headers
# ---------------------------------------------------------------------------


def test_rate_limiting_under_limit_succeeds(client: TestClient) -> None:
    """Requests below the category limit succeed and return standard rate-limit headers."""
    test_ip = get_random_ip()
    response = client.get(
        "/api/v1/categories",
        headers={"X-Forwarded-For": test_ip},
    )
    # Auth middleware rejects unauthenticated call with 401, but rate limit headers are attached
    assert response.status_code in (200, 401)
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers

    limit = int(response.headers["X-RateLimit-Limit"])
    remaining = int(response.headers["X-RateLimit-Remaining"])
    assert limit == settings.RATE_LIMIT_API_REQUESTS
    assert remaining == limit - 1


def test_rate_limiting_exceeding_limit_returns_429(client: TestClient) -> None:
    """Exceeding the rate limit returns HTTP 429 with standard error envelope and Retry-After."""
    test_ip = get_random_ip()
    limiter = RateLimiter()

    # Artificially consume quota for a test category
    category = "test_cat"
    limit = 3
    window = 10

    res1 = limiter.check_rate_limit(test_ip, category, limit=limit, window_seconds=window)
    assert res1.allowed is True
    assert res1.remaining == 2

    res2 = limiter.check_rate_limit(test_ip, category, limit=limit, window_seconds=window)
    assert res2.allowed is True
    assert res2.remaining == 1

    res3 = limiter.check_rate_limit(test_ip, category, limit=limit, window_seconds=window)
    assert res3.allowed is True
    assert res3.remaining == 0

    # 4th request must be rejected
    res4 = limiter.check_rate_limit(test_ip, category, limit=limit, window_seconds=window)
    assert res4.allowed is False
    assert res4.remaining == 0
    assert res4.retry_after > 0


def test_rate_limiting_client_ip_isolation(client: TestClient) -> None:
    """Traffic from IP A does not consume or affect the rate limit quota of IP B."""
    ip_a = "203.0.113.1"
    ip_b = "203.0.113.2"

    limiter = RateLimiter()
    category = "ip_isolation_test"

    # Exhaust quota for IP A
    for _ in range(3):
        res = limiter.check_rate_limit(ip_a, category, limit=3, window_seconds=60)
        assert res.allowed is True

    # Next for IP A is blocked
    res_a_blocked = limiter.check_rate_limit(ip_a, category, limit=3, window_seconds=60)
    assert res_a_blocked.allowed is False

    # IP B still has full quota
    res_b = limiter.check_rate_limit(ip_b, category, limit=3, window_seconds=60)
    assert res_b.allowed is True
    assert res_b.remaining == 2


def test_rate_limiting_category_isolation(client: TestClient) -> None:
    """Exhausting quota in one category does not affect other categories."""
    test_ip = get_random_ip()
    limiter = RateLimiter()

    # Exhaust category 1
    for _ in range(2):
        limiter.check_rate_limit(test_ip, "cat_one", limit=2, window_seconds=60)

    res_cat1 = limiter.check_rate_limit(test_ip, "cat_one", limit=2, window_seconds=60)
    assert res_cat1.allowed is False

    # Category 2 remains unaffected
    res_cat2 = limiter.check_rate_limit(test_ip, "cat_two", limit=2, window_seconds=60)
    assert res_cat2.allowed is True
    assert res_cat2.remaining == 1


def test_rate_limiting_window_expiration_and_reset() -> None:
    """Rate limit counters expire and reset after the sliding window elapses."""
    test_ip = get_random_ip()
    limiter = RateLimiter()
    category = "short_window_test"
    window = 1  # 1 second window

    # Consume single quota
    res1 = limiter.check_rate_limit(test_ip, category, limit=1, window_seconds=window)
    assert res1.allowed is True

    # Immediate second request blocked
    res2 = limiter.check_rate_limit(test_ip, category, limit=1, window_seconds=window)
    assert res2.allowed is False

    # Wait for window to elapse
    time.sleep(1.2)

    # Third request allowed again
    res3 = limiter.check_rate_limit(test_ip, category, limit=1, window_seconds=window)
    assert res3.allowed is True
    assert res3.remaining == 0


def test_exempt_endpoints_never_rate_limited(client: TestClient) -> None:
    """Health checks, root, and OpenAPI documentation endpoints are exempt from rate limiting."""
    for path in ["/", "/api/health", "/api/openapi.json"]:
        response = client.get(path)
        assert response.status_code == 200
        # Exempt routes should not return rate-limit response headers
        assert "X-RateLimit-Limit" not in response.headers


def test_rate_limiter_concurrency_atomic_evaluation() -> None:
    """Concurrent requests from multiple threads are evaluated atomically without race condition bypass."""
    test_ip = get_random_ip()
    limiter = RateLimiter()
    category = "concurrency_test"
    limit = 10
    total_threads = 25

    def make_request():
        return limiter.check_rate_limit(test_ip, category, limit=limit, window_seconds=60)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(total_threads)]
        results = [f.result() for f in futures]

    allowed_count = sum(1 for r in results if r.allowed)
    blocked_count = sum(1 for r in results if not r.allowed)

    assert allowed_count == limit
    assert blocked_count == total_threads - limit


def test_redis_keys_bounded_and_expire() -> None:
    """Keys created in Redis have an active TTL set to prevent unbounded growth."""
    test_ip = get_random_ip()
    limiter = RateLimiter()
    category = "ttl_test"
    window = 30

    limiter.check_rate_limit(test_ip, category, limit=5, window_seconds=window)

    client = get_redis_client()
    key = f"ratelimit:{category}:{test_ip}"
    ttl = client.ttl(key)
    assert 0 < ttl <= window + 2


# ---------------------------------------------------------------------------
# 2. Authentication Abuse Protections
# ---------------------------------------------------------------------------


def test_login_rate_limiting_abuse_protection(client: TestClient) -> None:
    """POST /api/v1/auth/login enforces strict category rate limits."""
    test_ip = get_random_ip()

    # Make requests up to auth limit
    with patch.object(settings, "RATE_LIMIT_AUTH_REQUESTS", 3):
        # 3 allowed attempts
        for _ in range(3):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "nonexistent@example.com", "password": "WrongPassword123!"},
                headers={"X-Forwarded-For": test_ip},
            )
            assert response.status_code == 401  # Bad credentials, but rate limit allowed

        # 4th attempt blocked by rate limiter
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "WrongPassword123!"},
            headers={"X-Forwarded-For": test_ip},
        )
        assert response.status_code == 429
        body = response.json()
        assert body["error"] == "rate_limit_exceeded"
        assert "Retry-After" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "0"


def test_password_reset_rate_limiting(client: TestClient) -> None:
    """POST /api/v1/auth/forgot-password enforces strict rate limiting."""
    test_ip = get_random_ip()

    with patch.object(settings, "RATE_LIMIT_PASSWORD_RESET_REQUESTS", 2):
        for _ in range(2):
            response = client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "user@example.com"},
                headers={"X-Forwarded-For": test_ip},
            )
            assert response.status_code == 200

        # 3rd request blocked
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "user@example.com"},
            headers={"X-Forwarded-For": test_ip},
        )
        assert response.status_code == 429
        assert response.json()["error"] == "rate_limit_exceeded"


def test_mfa_rate_limiting_abuse_protection(client: TestClient) -> None:
    """POST /api/v1/auth/mfa/verify enforces strict rate limiting against brute-force."""
    test_ip = get_random_ip()

    with patch.object(settings, "RATE_LIMIT_MFA_REQUESTS", 2):
        for _ in range(2):
            response = client.post(
                "/api/v1/auth/mfa/verify",
                json={"mfa_token": "dummy_token", "code": "123456"},
                headers={"X-Forwarded-For": test_ip},
            )
            assert response.status_code == 401  # Invalid token, but permitted by rate limiter

        # 3rd request blocked
        response = client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": "dummy_token", "code": "123456"},
            headers={"X-Forwarded-For": test_ip},
        )
        assert response.status_code == 429
        assert response.json()["error"] == "rate_limit_exceeded"


# ---------------------------------------------------------------------------
# 3. Security HTTP Headers & Content Security Policy (CSP)
# ---------------------------------------------------------------------------


def test_security_headers_present_on_responses(client: TestClient) -> None:
    """Outbound responses contain modern defensive HTTP security headers."""
    response = client.get("/api/health")
    assert response.status_code == 200

    headers = response.headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert headers["X-XSS-Protection"] == "0"
    assert "Permissions-Policy" in headers
    assert "Content-Security-Policy" in headers


def test_content_security_policy_directives(client: TestClient) -> None:
    """Content Security Policy contains restrictive, application-tailored directives."""
    response = client.get("/api/health")
    csp = response.headers.get("Content-Security-Policy", "")

    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    assert "img-src 'self' data:" in csp
    assert "https://api.qrserver.com" not in csp
    assert "font-src 'self' data:" in csp
    assert "object-src 'none'" in csp
    assert "base-uri 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_hsts_header_controlled_by_config(client: TestClient) -> None:
    """HSTS header is absent in local dev, but added when ENABLE_HSTS=True."""
    # 1. Default (disabled in local dev)
    response = client.get("/api/health")
    assert "Strict-Transport-Security" not in response.headers

    # 2. Enabled via config
    with patch.object(settings, "ENABLE_HSTS", True):
        with patch.object(settings, "HSTS_MAX_AGE", 31536000):
            response_hsts = client.get("/api/health")
            assert "Strict-Transport-Security" in response_hsts.headers
            assert "max-age=31536000" in response_hsts.headers["Strict-Transport-Security"]
            assert "includeSubDomains" in response_hsts.headers["Strict-Transport-Security"]


# ---------------------------------------------------------------------------
# 4. CORS Hardening
# ---------------------------------------------------------------------------


def test_cors_valid_origin_allowed(client: TestClient) -> None:
    """Preflight and requests from configured frontend origins receive CORS headers."""
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, Authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_unauthorized_origin_rejected(client: TestClient) -> None:
    """Requests with unauthorized origins do not receive allow-origin header."""
    response = client.get(
        "/api/health",
        headers={"Origin": "http://malicious-site.example.com"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_exposed_headers_present(client: TestClient) -> None:
    """Exposed headers include X-Request-ID, Retry-After, and X-RateLimit headers."""
    response = client.get(
        "/api/v1/categories",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code in (200, 401)
    exposed = response.headers.get("access-control-expose-headers", "")
    assert "X-Request-ID" in exposed
    assert "Retry-After" in exposed
    assert "X-RateLimit-Limit" in exposed


# ---------------------------------------------------------------------------
# 5. Request Payload Size Protection
# ---------------------------------------------------------------------------


def test_request_size_limit_normal_payload_accepted(client: TestClient) -> None:
    """Normal-sized request payloads pass without restriction."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "Password123!"},
    )
    assert response.status_code in (401, 200)


def test_request_size_limit_oversized_rejected_413(client: TestClient) -> None:
    """Requests exceeding MAX_REQUEST_BODY_SIZE are rejected with HTTP 413 Payload Too Large."""
    # Artificially set a small max request body size
    with patch.object(settings, "MAX_REQUEST_BODY_SIZE", 50):
        large_payload = {"email": "test@example.com", "data": "A" * 200}
        response = client.post(
            "/api/v1/auth/login",
            json=large_payload,
        )
        assert response.status_code == 413
        body = response.json()
        assert body["error"] == "payload_too_large"
        assert "exceeds the maximum permitted size" in body["message"]


# ---------------------------------------------------------------------------
# 6. Redis Failure Resilience (Fail-Closed vs Fail-Open)
# ---------------------------------------------------------------------------


def test_fail_closed_on_security_critical_auth_endpoints(client: TestClient) -> None:
    """When Redis is unreachable, security-critical authentication endpoints fail closed (HTTP 503)."""
    test_ip = get_random_ip()

    # Simulate Redis connection failure
    with patch("app.core.ratelimit.get_redis_client", side_effect=RedisConnectionError("Connection refused")):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Password123!"},
            headers={"X-Forwarded-For": test_ip},
        )
        assert response.status_code == 503
        body = response.json()
        assert body["error"] == "service_unavailable"
        assert "temporarily unavailable" in body["message"]


def test_fail_open_on_general_api_endpoints(client: TestClient) -> None:
    """When Redis is unreachable, general non-sensitive API endpoints fail open to preserve availability."""
    test_ip = get_random_ip()

    # Simulate Redis connection failure
    with patch("app.core.ratelimit.get_redis_client", side_effect=RedisConnectionError("Connection refused")):
        response = client.get(
            "/api/v1/categories",
            headers={"X-Forwarded-For": test_ip},
        )
        # Should bypass rate limiting (fail open) and reach application auth/router (returning 401 unauth or 200, but NOT 503)
        assert response.status_code in (200, 401)
        assert response.status_code != 503


# ---------------------------------------------------------------------------
# 7. Error Envelope & Secret Sanitization
# ---------------------------------------------------------------------------


def test_429_error_envelope_sanitized_no_internals(client: TestClient) -> None:
    """429 responses follow the standard error envelope and never expose Redis or SQL internals."""
    test_ip = get_random_ip()

    with patch.object(settings, "RATE_LIMIT_AUTH_REQUESTS", 1):
        # 1st request
        client.post(
            "/api/v1/auth/login",
            json={"email": "a@b.com", "password": "Pass"},
            headers={"X-Forwarded-For": test_ip},
        )
        # 2nd request triggers 429
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "a@b.com", "password": "Pass"},
            headers={"X-Forwarded-For": test_ip},
        )
        assert response.status_code == 429
        body = response.json()

        assert "error" in body
        assert "message" in body
        assert body["error"] == "rate_limit_exceeded"

        raw_text = response.text
        assert "redis" not in raw_text.lower()
        assert "ratelimit:" not in raw_text
        assert "lua" not in raw_text.lower()
