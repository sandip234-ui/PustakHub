"""
Audit Context & Security Request Middleware.

Responsibilities:
  - Generates a unique Request-ID for distributed tracing and audit correlation.
  - Extracts and normalizes client IP address and User-Agent headers.
  - Attaches audit metadata to `request.state` for route handlers and audit services.
"""

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that populates request context (IP, User-Agent, Request-ID)
    used for non-intrusive, tamper-resistant audit logging.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or preserve X-Request-ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Extract client IP respecting standard reverse-proxy headers if configured
        client_ip = request.headers.get("X-Forwarded-For")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = None

        request.state.client_ip = client_ip
        request.state.user_agent = request.headers.get("user-agent")

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
