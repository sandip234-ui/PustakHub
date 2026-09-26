"""
Security HTTP Headers & Content Security Policy (CSP) Middleware for PustakHub.

Applies modern defense-in-depth HTTP security headers to all outbound responses.
"""

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware injecting modern security headers and Content Security Policy (CSP).
    """

    def _build_csp_header(self) -> str:
        """Construct the Content Security Policy directive string."""
        if settings.CSP_DIRECTIVES:
            return settings.CSP_DIRECTIVES

        # Connect sources include self plus any explicitly configured CORS origins
        connect_sources = ["'self'"]
        for origin in settings.cors_origins_list:
            if origin and origin != "*":
                connect_sources.append(origin)

        connect_src_directive = " ".join(connect_sources)

        directives = [
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data:",
            "font-src 'self' data:",
            f"connect-src {connect_src_directive}",
            "object-src 'none'",
            "base-uri 'self'",
            "frame-ancestors 'none'",
        ]
        return "; ".join(directives)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        if not settings.ENABLE_SECURITY_HEADERS:
            return response

        # Modern standard security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), "
            "microphone=(), payment=(), usb=()"
        )

        # Content Security Policy (CSP)
        if settings.ENABLE_CSP:
            response.headers["Content-Security-Policy"] = self._build_csp_header()

        # HTTP Strict Transport Security (HSTS) — enabled in production/HTTPS environments
        if settings.ENABLE_HSTS:
            hsts_val = f"max-age={settings.HSTS_MAX_AGE}"
            if settings.HSTS_INCLUDE_SUBDOMAINS:
                hsts_val += "; includeSubDomains"
            response.headers["Strict-Transport-Security"] = hsts_val

        return response
