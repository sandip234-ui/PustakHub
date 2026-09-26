"""
Authentication and registration HTTP router.

Endpoints:
  - POST /api/v1/auth/register          - Public student registration (triggers OTP email)
  - POST /api/v1/auth/verify-otp        - Verify 6-digit OTP and provision PostgreSQL user
  - POST /api/v1/auth/login             - Authenticate with email/password (supports MFA challenge)
  - POST /api/v1/auth/refresh           - Rotate refresh token and issue new access token
  - POST /api/v1/auth/logout            - Invalidate refresh-token session
  - GET  /api/v1/auth/me                - Retrieve current authenticated user profile
  - POST /api/v1/auth/forgot-password   - Request password reset email
  - POST /api/v1/auth/reset-password    - Set new password using single-use reset token
  - POST /api/v1/auth/mfa/enroll        - Generate TOTP secret and backup recovery codes
  - POST /api/v1/auth/mfa/verify-enrollment - Verify initial TOTP code and enable MFA
  - POST /api/v1/auth/mfa/verify        - Solve MFA login challenge with TOTP/recovery code
  - POST /api/v1/auth/mfa/disable       - Disable MFA (requires password verification)
  - GET  /api/v1/auth/mfa/status        - Query user MFA status
"""

from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.modules.auth.dependencies import get_current_user, security_scheme
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MessageResponse,
    MfaDisableRequest,
    MfaEnrollResponse,
    MfaStatusResponse,
    MfaVerifyEnrollmentRequest,
    MfaVerifyRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserOut,
    VerifyOtpRequest,
    VerifyOtpResponse,
)
from app.modules.auth.service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate student registration",
    description=(
        "Registers a new student by storing state temporarily in Redis and dispatching "
        "a 6-digit email OTP. The PostgreSQL user is NOT created until OTP verification succeeds."
    ),
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    return auth_service.initiate_registration(db, data)


@router.post(
    "/verify-otp",
    response_model=VerifyOtpResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Verify registration OTP",
    description=(
        "Submits the 6-digit OTP sent via email. Upon verification, the user account is created "
        "in PostgreSQL with the STUDENT role, activated, and Redis temporary state is cleaned up."
    ),
)
def verify_otp(
    data: VerifyOtpRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> VerifyOtpResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_service.verify_registration_otp(
        db, data, client_ip=client_ip, user_agent=user_agent
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description=(
        "Authenticates user credentials using Argon2id verification. "
        "If MFA is enabled on the account, returns an MFA challenge token. "
        "Otherwise, issues short-lived JWT access and refresh tokens."
    ),
)
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> LoginResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_service.authenticate_user(db, data, client_ip=client_ip, user_agent=user_agent)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description=(
        "Submits an existing refresh token to perform token rotation. "
        "Revokes the previous session and returns a new access and refresh token pair."
    ),
)
def refresh(
    data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_service.refresh_tokens(
        db, data.refresh_token, client_ip=client_ip, user_agent=user_agent
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Revokes the specified refresh-token session on the server.",
)
def logout(
    data: LogoutRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> MessageResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    auth_service.revoke_session(
        db,
        refresh_token_str=data.refresh_token,
        client_ip=client_ip,
        user_agent=user_agent,
    )
    return MessageResponse(message="Logged out successfully.")


@router.get(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Current authenticated user profile",
    description="Returns the profile details and assigned roles of the currently authenticated user.",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    return UserOut(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        account_status=current_user.account_status.value,
        roles=[r.name for r in current_user.roles],
        is_mfa_enabled=current_user.is_mfa_enabled,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
    )


# ===========================================================================
# Password Reset Endpoints (Phase 7)
# ===========================================================================


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description=(
        "Initiates the password reset workflow by generating a cryptographically secure, "
        "short-lived reset token and emailing instructions to the user. "
        "Returns a generic response to prevent account enumeration."
    ),
)
def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> MessageResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_service.initiate_password_reset(
        db, data, client_ip=client_ip, user_agent=user_agent
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset account password",
    description=(
        "Validates the single-use password reset token, updates the password using Argon2id, "
        "invalidates all existing refresh-token sessions, and marks the token consumed."
    ),
)
def reset_password(
    data: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> MessageResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_service.complete_password_reset(
        db, data, client_ip=client_ip, user_agent=user_agent
    )


# ===========================================================================
# Multi-Factor Authentication (MFA) Endpoints (Phase 7)
# ===========================================================================


@router.post(
    "/mfa/enroll",
    response_model=MfaEnrollResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate MFA enrollment",
    description=(
        "Generates a base32 TOTP secret, otpauth URI, and one-time backup recovery codes. "
        "MFA is NOT activated until the user submits a valid verification code."
    ),
)
def mfa_enroll(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MfaEnrollResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_service.enroll_mfa(
        db, current_user, client_ip=client_ip, user_agent=user_agent
    )


@router.post(
    "/mfa/verify-enrollment",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify MFA enrollment and activate",
    description="Submits the initial 6-digit TOTP code to finalize and enable MFA on the account.",
)
def mfa_verify_enrollment(
    data: MfaVerifyEnrollmentRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_service.verify_mfa_enrollment(
        db, current_user, data, client_ip=client_ip, user_agent=user_agent
    )


@router.post(
    "/mfa/verify",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify MFA login challenge",
    description="Submits a TOTP code or one-time recovery code to satisfy an active login challenge.",
)
def mfa_verify(
    data: MfaVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> LoginResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_service.verify_mfa_login(
        db, data, client_ip=client_ip, user_agent=user_agent
    )


@router.post(
    "/mfa/disable",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Disable MFA",
    description="Disables two-factor authentication on the account. Requires password re-authentication.",
)
def mfa_disable(
    data: MfaDisableRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_service.disable_mfa(
        db, current_user, data, client_ip=client_ip, user_agent=user_agent
    )


@router.get(
    "/mfa/status",
    response_model=MfaStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get MFA status",
    description="Returns whether MFA is enabled for the authenticated user without exposing secrets.",
)
def mfa_status(
    current_user: User = Depends(get_current_user),
) -> MfaStatusResponse:
    return auth_service.get_mfa_status(current_user)

