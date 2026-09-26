"""
PustakHub — FastAPI Application Entry Point.

Responsibilities of this file:
  - Create the FastAPI application instance.
  - Register middleware (CORS, etc.).
  - Register exception handlers.
  - Mount routers (added in later phases via app.include_router).
  - Define the application lifespan (startup / shutdown hooks).

Business logic must NOT live here. Keep this file thin.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import check_database_connection
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.redis import check_redis_connection

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Startup logic runs before `yield`; shutdown logic runs after.
    Future phases will add:
      - Database connection pool initialisation
      - Redis connection check
    """
    configure_logging()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Debug mode: %s", settings.DEBUG)
    logger.info("Allowed CORS origins: %s", settings.cors_origins_list)

    # Verify database connectivity at startup (non-blocking — app starts even if DB is down)
    db_ok = check_database_connection()
    if db_ok:
        logger.info("Database connectivity: OK")
        # Ensure default roles and permissions are initialized and synchronized
        try:
            from app.core.database import SessionLocal
            from app.modules.permissions.service import permission_service
            with SessionLocal() as db:
                permission_service.seed_default_roles_and_permissions(db)
        except Exception as exc:
            logger.error("Error during initial RBAC roles/permissions synchronization: %s", exc)
    else:
        logger.warning(
            "Database connectivity: FAILED. "
            "Check DATABASE_URL in .env. Application will start without DB access."
        )

    # Check Redis connectivity at startup
    redis_ok = check_redis_connection()
    if redis_ok:
        logger.info("Redis connectivity: OK")
        try:
            from app.modules.realtime.redis_subscriber import start_redis_subscriber
            start_redis_subscriber()
        except Exception as exc:
            logger.debug("Could not start Redis realtime subscriber: %s", exc)
    else:
        logger.warning(
            "Redis connectivity: FAILED. "
            "Check REDIS_URL in .env. Temporary registration state requires Redis."
        )

    yield  # Application runs here

    try:
        from app.modules.realtime.redis_subscriber import stop_redis_subscriber
        stop_redis_subscriber()
    except Exception:
        pass

    logger.info("Shutting down %s", settings.APP_NAME)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns a fully configured FastAPI instance ready to be served.
    """
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "PustakHub — Secure Library & Identity Management Platform. "
            "API documentation for internal and future external use."
        ),
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # --- Security & Rate Limiting Middleware Stack ---
    # Execution order (innermost to outermost):
    # SecurityHeaders -> RateLimit -> AuditContext -> RequestSizeLimit -> CORS
    from app.middleware import (
        AuditContextMiddleware,
        RateLimitMiddleware,
        RequestSizeLimitMiddleware,
        SecurityHeadersMiddleware,
    )

    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(RateLimitMiddleware)
    application.add_middleware(AuditContextMiddleware)
    application.add_middleware(RequestSizeLimitMiddleware)

    # --- Hardened CORS ---
    # Explicit origins, strict method and header whitelist, exposed security headers
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Accept", "Origin", "X-Requested-With"],
        expose_headers=[
            "X-Request-ID",
            "Retry-After",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
        max_age=600,
    )

    # --- Exception handlers ---
    register_exception_handlers(application)

    # --- Routers ---
    from app.modules.audit.router import router as audit_router
    from app.modules.auth.router import router as auth_router
    from app.modules.books.router import (
        book_router,
        category_router,
        copy_router,
    )
    from app.modules.borrowing.router import router as borrowing_router
    from app.modules.fines.router import router as fines_router
    from app.modules.permissions.router import router as permissions_router
    from app.modules.realtime.router import router as realtime_router
    from app.modules.roles.router import router as roles_router
    from app.modules.users.router import router as users_router

    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(roles_router, prefix="/api/v1")
    application.include_router(permissions_router, prefix="/api/v1")
    application.include_router(audit_router, prefix="/api/v1")
    application.include_router(users_router, prefix="/api/v1")
    application.include_router(category_router, prefix="/api/v1")
    application.include_router(book_router, prefix="/api/v1")
    application.include_router(copy_router, prefix="/api/v1")
    application.include_router(borrowing_router, prefix="/api/v1")
    application.include_router(fines_router, prefix="/api/v1")
    application.include_router(realtime_router, prefix="/api/v1")

    return application


app = create_application()


# ---------------------------------------------------------------------------
# Built-in endpoints
# ---------------------------------------------------------------------------


@app.get("/", tags=["root"], include_in_schema=False)
async def root() -> dict:
    """Root endpoint — not part of the versioned API."""
    return {
        "project": settings.APP_NAME,
        "message": f"Welcome to {settings.APP_NAME} API",
        "status": "running",
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
    }


@app.get("/api/health", tags=["health"])
async def health() -> dict:
    """
    Health check endpoint.

    Returns the operational status of the PustakHub backend.
    Database and Redis connectivity are checked on every call.

    SECURITY: DATABASE_URL, credentials, and connection strings are
    NEVER returned in the response body.
    """
    db_healthy = check_database_connection()
    redis_healthy = check_redis_connection()
    overall_status = "healthy" if (db_healthy and redis_healthy) else "degraded"

    return {
        "status": overall_status,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "backend": "FastAPI",
        "database": "healthy" if db_healthy else "unreachable",
        "redis": "healthy" if redis_healthy else "unreachable",
    }