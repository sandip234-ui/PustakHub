import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure tests run against the dedicated test database
TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://sandipbiswal@localhost:5432/pustakhub_test",
)
os.environ["DATABASE_URL"] = TEST_DB_URL

from app.core.config import settings
settings.DATABASE_URL = TEST_DB_URL

import app.core.database as db_module

# Point the application's engine and SessionLocal to the test database
test_engine = create_engine(
    TEST_DB_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=1800,
    future=True,
)
test_session_local = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Overwrite in database module
db_module.engine = test_engine
db_module.SessionLocal = test_session_local

from app.core.redis import get_redis_client
from app.main import app
from app.models.base import Base
from app.modules.permissions.service import permission_service


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Verify test database connection and seed baseline roles/permissions."""
    # Safety guard: Ensure we are NEVER running tests on the development DB
    assert "test" in settings.DATABASE_URL.lower(), (
        f"SAFETY GUARD TRIGGERED: Tests must run against a test database, got {settings.DATABASE_URL}"
    )
    
    # Ensure all tables exist in test database
    Base.metadata.create_all(bind=test_engine)
    
    with test_session_local() as db:
        permission_service.seed_default_roles_and_permissions(db)
    
    yield


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    Session-scoped FastAPI test client.

    Uses a single client instance for the entire test session to avoid
    repeated application startup overhead.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_redis_ratelimits_global():
    """Flush rate limit keys in Redis before and after each test."""
    try:
        r = get_redis_client()
        keys = r.keys("ratelimit:*")
        if keys:
            r.delete(*keys)
    except Exception:
        pass
    yield
    try:
        r = get_redis_client()
        keys = r.keys("ratelimit:*")
        if keys:
            r.delete(*keys)
    except Exception:
        pass

