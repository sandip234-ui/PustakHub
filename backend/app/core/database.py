"""
SQLAlchemy engine, session factory, and FastAPI session dependency.

This module provides the single database connection entry point.
All database access in the application must use the `get_db` dependency
(or the session factory directly in background tasks).

SECURITY:
- DATABASE_URL is loaded exclusively from environment variables.
- It is never logged, printed, or exposed through any API endpoint.
- Connection errors are caught and re-raised without leaking the URL.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

_db_url = settings.DATABASE_URL

if not _db_url:
    logger.warning(
        "DATABASE_URL is not set. Database features will be unavailable. "
        "Set DATABASE_URL in .env to enable database connectivity."
    )

engine = create_engine(
    _db_url or "postgresql+psycopg://",  # placeholder keeps engine import-safe
    # Connection pool settings suited for a FastAPI / Uvicorn deployment.
    pool_pre_ping=True,       # test connections before handing them from the pool
    pool_size=5,              # idle connections kept open
    max_overflow=10,          # connections allowed above pool_size under load
    pool_recycle=1800,        # recycle connections after 30 minutes
    echo=settings.DEBUG,      # log SQL in debug mode only (never in production)
    future=True,              # SQLAlchemy 2.0 style
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # avoid unexpected lazy-load after commit
)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a SQLAlchemy database session.

    Usage in a route:
        from fastapi import Depends
        from app.core.database import get_db

        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...

    The session is committed on success and rolled back on any exception,
    then always closed when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Connectivity helper (used by health endpoint)
# ---------------------------------------------------------------------------


def check_database_connection() -> bool:
    """
    Attempt a lightweight SELECT 1 to verify the database is reachable.

    Returns True if the database is healthy, False otherwise.
    Never raises — callers (e.g., the health endpoint) receive a safe boolean.
    Deliberately avoids logging any connection details.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        # Log only the exception type — never the DATABASE_URL or credentials.
        logger.warning("Database connectivity check failed: %s", type(exc).__name__)
        return False
