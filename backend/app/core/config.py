"""
Application configuration.

Uses pydantic-settings to load values from environment variables
or a .env file. Provides safe development defaults.

SECURITY NOTES:
- Never hardcode production secrets here.
- All sensitive values must come from environment variables.
- The .env file must never be committed to version control.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application settings.

    Values are loaded in order of priority:
      1. Actual environment variables
      2. .env file
      3. Default values defined below
    """

    # --- Application ---
    APP_NAME: str = "PustakHub"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- CORS ---
    # Comma-separated list of allowed origins.
    # In production, set this to your real frontend domain(s) via env var.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"

    # --- Frontend ---
    FRONTEND_URL: str = "http://localhost:5174"

    # --- Database (Phase 2) ---
    DATABASE_URL: str = ""

    # --- Redis (Phase 3: Temporary Registration & OTP) ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- JWT (Phase 3: Authentication) ---
    JWT_SECRET: str = "dev-insecure-jwt-secret-key-must-be-overridden-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- OTP (Phase 3: Registration Verification) ---
    OTP_EXPIRE_MINUTES: int = 5
    MAX_OTP_ATTEMPTS: int = 5

    # --- Password Reset & MFA (Phase 7 & Phase 9 Hardening) ---
    PASSWORD_RESET_EXPIRE_MINUTES: int = 15
    MFA_ISSUER_NAME: str = "PustakHub"
    MFA_ENCRYPTION_KEY: str = "dev-insecure-mfa-encryption-key-32-bytes-long!"

    # --- Circulation (Phase 6: Borrowing & Fines) ---
    DEFAULT_LOAN_PERIOD_DAYS: int = 14
    DAILY_FINE_RATE: float = 2.00
    MAX_ACTIVE_BORROWS_PER_USER: int = 5

    # --- SMTP (Phase 3: Email OTP Delivery) ---
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@pustakhub.local"
    SMTP_FROM_NAME: str = "PustakHub"
    SMTP_USE_TLS: bool = True

    # --- Rate Limiting (Phase 8) ---
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_REQUESTS: int = 20
    RATE_LIMIT_AUTH_WINDOW_SECONDS: int = 60
    RATE_LIMIT_REGISTER_REQUESTS: int = 20
    RATE_LIMIT_REGISTER_WINDOW_SECONDS: int = 60
    RATE_LIMIT_PASSWORD_RESET_REQUESTS: int = 20
    RATE_LIMIT_PASSWORD_RESET_WINDOW_SECONDS: int = 60
    RATE_LIMIT_MFA_REQUESTS: int = 20
    RATE_LIMIT_MFA_WINDOW_SECONDS: int = 60
    RATE_LIMIT_API_REQUESTS: int = 200
    RATE_LIMIT_API_WINDOW_SECONDS: int = 60
    RATE_LIMIT_FAIL_CLOSED_AUTH: bool = True

    # --- Security Hardening & Headers (Phase 8) ---
    MAX_REQUEST_BODY_SIZE: int = 2 * 1024 * 1024  # 2MB
    ENABLE_SECURITY_HEADERS: bool = True
    ENABLE_CSP: bool = True
    CSP_DIRECTIVES: str = ""
    ENABLE_HSTS: bool = False
    HSTS_MAX_AGE: int = 31536000
    HSTS_INCLUDE_SUBDOMAINS: bool = True
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        # Extra env vars are silently ignored
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS from comma-separated string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


# Single shared settings instance — import this everywhere.
settings = Settings()
