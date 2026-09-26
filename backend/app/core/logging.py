"""
Application logging configuration.

Sets up structured console logging for development.

SECURITY RULES (must be enforced throughout the codebase):
- NEVER log passwords, OTP values, raw credentials, or secret keys.
- NEVER log JWT access tokens or refresh tokens.
- NEVER log database connection strings with embedded passwords.
- Log user IDs and usernames are acceptable; do NOT log password hashes.
"""

import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """
    Configure the root logger for PustakHub.

    Should be called once at application startup (in main.py lifespan).
    """
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )

    # Suppress overly verbose third-party loggers in production.
    if not settings.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.

    Usage:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened")
    """
    return logging.getLogger(name)
