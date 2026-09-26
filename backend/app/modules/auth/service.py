"""
Authentication and registration business logic service.

Encapsulates:
  - Temporary Redis registration storage with Argon2id password & OTP hashing
  - Email OTP dispatch & throttled verification
  - PostgreSQL User creation with hardcoded STUDENT role upon OTP verification
  - Login authentication & account status checks
  - JWT access token generation & refresh-token session management (UserSession)
  - Refresh-token rotation and revocation (logout)

SECURITY:
  - User records are NEVER created in PostgreSQL prior to successful OTP verification.
  - Refresh tokens are stored ONLY as SHA-256 hashes in `user_sessions`.
  - Raw passwords and OTPs are never stored or logged.
  - Constant-time verification is used to prevent timing attacks.
"""

import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError
import pyotp
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email import email_service
from app.core.logging import get_logger
from app.core.encryption import decrypt_mfa_secret, encrypt_mfa_secret
from app.core.redis import get_redis_client
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp,
    hash_otp,
    hash_password,
    hash_token,
    verify_otp_hash,
    verify_password,
)
from app.models.audit_log import AuditAction, AuditStatus
from app.models.role import Role
from app.models.session import UserSession
from app.models.user import AccountStatus, User
from app.modules.audit.service import audit_service
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    MfaDisableRequest,
    MfaEnrollResponse,
    MfaStatusResponse,
    MfaVerifyEnrollmentRequest,
    MfaVerifyRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserOut,
    VerifyOtpRequest,
    VerifyOtpResponse,
)

logger = get_logger(__name__)

# Dummy Argon2id hash used to mitigate timing attacks on nonexistent users
_DUMMY_ARGON2_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$anVzdGFkdW1teXNhbHQ$g6YF57Q2k/3XnBsmw90U+eG7h/8xM9p0L1w6z6"
)


class AuthService:
    """Core authentication, registration, and session management service."""

    @staticmethod
    def initiate_registration(db: Session, data: RegisterRequest) -> RegisterResponse:
        """
        Initiate student registration by storing state in Redis and dispatching an OTP.

        A PostgreSQL User row is NOT created at this stage.
        """
        email = data.email.strip().lower()

        # Check if an active user with this email already exists in PostgreSQL
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user and existing_user.account_status == AccountStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists.",
            )

        # Hash password with Argon2id before placing in Redis
        password_hash = hash_password(data.password)

        # Generate cryptographically secure 6-digit OTP and compute its SHA-256 hash
        otp = generate_otp(6)
        otp_digest = hash_otp(otp)

        # Build temporary registration payload
        now_utc = datetime.now(timezone.utc)
        expires_at = now_utc + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        reg_data = {
            "name": data.name.strip(),
            "email": email,
            "password_hash": password_hash,
            "otp_hash": otp_digest,
            "otp_attempts": 0,
            "created_at": now_utc.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        # Store in Redis with TTL
        redis_key = f"registration:{email}"
        try:
            redis_client = get_redis_client()
            redis_client.set(
                redis_key,
                json.dumps(reg_data),
                ex=settings.OTP_EXPIRE_MINUTES * 60,
            )
        except RedisError as exc:
            logger.error("Redis error while storing registration for %s: %s", email, exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Registration service temporarily unavailable. Please try again.",
            )

        # Dispatch OTP via email service
        email_service.send_registration_otp(
            to_email=email,
            recipient_name=data.name.strip(),
            otp=otp,
        )

        return RegisterResponse(
            message="Verification code sent. Please check your email to complete registration.",
            email=email,
        )

    @staticmethod
    def verify_registration_otp(
        db: Session,
        data: VerifyOtpRequest,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> VerifyOtpResponse:
        """
        Verify the submitted OTP against Redis temporary storage.

        Upon successful verification:
          1. Creates the User record in PostgreSQL.
          2. Server-side assigns the STUDENT role.
          3. Sets account status to ACTIVE.
          4. Deletes the temporary Redis record.
          5. Records a USER_CREATED audit log event.
        """
        email = data.email.strip().lower()
        redis_key = f"registration:{email}"

        try:
            redis_client = get_redis_client()
            cached_data = redis_client.get(redis_key)
        except RedisError as exc:
            logger.error("Redis error during OTP lookup for %s: %s", email, exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Verification service temporarily unavailable. Please try again.",
            )

        if not cached_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired or registration was not found. Please register again.",
            )

        try:
            reg_dict = json.loads(cached_data)
        except json.JSONDecodeError:
            redis_client.delete(redis_key)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid registration state. Please register again.",
            )

        # Check maximum verification attempts
        attempts = reg_dict.get("otp_attempts", 0)
        if attempts >= settings.MAX_OTP_ATTEMPTS:
            redis_client.delete(redis_key)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum verification attempts exceeded. Please register again.",
            )

        # Verify OTP
        is_valid = verify_otp_hash(data.otp, reg_dict["otp_hash"])
        if not is_valid:
            # Increment attempts and update Redis preserving remaining TTL
            reg_dict["otp_attempts"] = attempts + 1
            remaining_attempts = max(0, settings.MAX_OTP_ATTEMPTS - reg_dict["otp_attempts"])
            ttl = redis_client.ttl(redis_key)
            if ttl > 0:
                redis_client.set(redis_key, json.dumps(reg_dict), ex=ttl)

            if remaining_attempts == 0:
                redis_client.delete(redis_key)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum verification attempts exceeded. Please register again.",
                )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid verification code. {remaining_attempts} attempt(s) remaining.",
            )

        # OTP verified! Create user in PostgreSQL
        # Ensure STUDENT role exists in database
        student_role = db.query(Role).filter(Role.name == "STUDENT").first()
        if not student_role:
            student_role = Role(
                name="STUDENT",
                description="Default student role with library borrowing privileges",
            )
            db.add(student_role)
            db.flush()

        # Handle edge case where user record was already created
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            if existing_user.account_status == AccountStatus.ACTIVE:
                redis_client.delete(redis_key)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User account already exists. Please log in.",
                )
            # If pending verification or deactivated, update password & activate
            existing_user.full_name = reg_dict["name"]
            existing_user.password_hash = reg_dict["password_hash"]
            existing_user.account_status = AccountStatus.ACTIVE
            if student_role not in existing_user.roles:
                existing_user.roles.append(student_role)
            user = existing_user
        else:
            user = User(
                full_name=reg_dict["name"],
                email=email,
                password_hash=reg_dict["password_hash"],
                account_status=AccountStatus.ACTIVE,
                roles=[student_role],
            )
            db.add(user)

        db.commit()
        db.refresh(user)

        # Clean up temporary registration in Redis
        try:
            redis_client.delete(redis_key)
        except Exception:
            pass  # Non-fatal

        # Audit log the user creation event
        audit_service.log(
            db=db,
            action=AuditAction.USER_CREATED,
            user_id=user.id,
            resource_type="User",
            resource_id=str(user.id),
            status=AuditStatus.SUCCESS,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        try:
            from app.modules.realtime.events import RealtimeEventType
            from app.modules.realtime.publisher import publish_realtime_event

            publish_realtime_event(
                event_type=RealtimeEventType.USER_CREATED,
                resource_type="User",
                resource_id=str(user.id),
                actor_user_id=user.id,
                target_user_id=user.id,
                data={"email": user.email, "full_name": user.full_name},
            )
        except Exception:
            pass

        logger.info("New student account verified and created: %s (%s)", user.email, user.id)

        return VerifyOtpResponse(
            message="Account verified and created successfully. You can now log in.",
            email=user.email,
            user_id=user.id,
        )

    @staticmethod
    def authenticate_user(
        db: Session,
        data: LoginRequest,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenResponse:
        """
        Authenticate user credentials and issue access + refresh tokens.

        Stores only the SHA-256 hash of the refresh token in UserSession.
        """
        email = data.email.strip().lower()
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Timing attack mitigation: run verification against dummy hash
            verify_password(data.password, _DUMMY_ARGON2_HASH)
            audit_service.log(
                db=db,
                action=AuditAction.LOGIN_FAILURE,
                user_id=None,
                resource_type="User",
                resource_id=email,
                status=AuditStatus.FAILURE,
                ip_address=client_ip,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(data.password, user.password_hash):
            audit_service.log(
                db=db,
                action=AuditAction.LOGIN_FAILURE,
                user_id=user.id,
                resource_type="User",
                resource_id=str(user.id),
                status=AuditStatus.FAILURE,
                ip_address=client_ip,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check account status
        if user.account_status == AccountStatus.PENDING_VERIFICATION:
            audit_service.log(
                db=db,
                action=AuditAction.LOGIN_FAILURE,
                user_id=user.id,
                resource_type="User",
                resource_id=str(user.id),
                status=AuditStatus.FAILURE,
                ip_address=client_ip,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account verification is pending. Please verify your email first.",
            )
        if user.account_status == AccountStatus.SUSPENDED:
            audit_service.log(
                db=db,
                action=AuditAction.LOGIN_FAILURE,
                user_id=user.id,
                resource_type="User",
                resource_id=str(user.id),
                status=AuditStatus.FAILURE,
                ip_address=client_ip,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is suspended. Please contact the library administrator.",
            )
        if user.account_status == AccountStatus.DEACTIVATED:
            audit_service.log(
                db=db,
                action=AuditAction.LOGIN_FAILURE,
                user_id=user.id,
                resource_type="User",
                resource_id=str(user.id),
                status=AuditStatus.FAILURE,
                ip_address=client_ip,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been deactivated.",
            )
        if user.account_status != AccountStatus.ACTIVE:
            audit_service.log(
                db=db,
                action=AuditAction.LOGIN_FAILURE,
                user_id=user.id,
                resource_type="User",
                resource_id=str(user.id),
                status=AuditStatus.FAILURE,
                ip_address=client_ip,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active.",
            )

        # Check if user has MFA enabled
        if user.is_mfa_enabled:
            # Generate short-lived MFA challenge token
            mfa_token = secrets.token_urlsafe(32)
            mfa_digest = hash_token(mfa_token)
            challenge_key = f"mfa_challenge:{mfa_digest}"
            challenge_payload = json.dumps({
                "user_id": str(user.id),
                "email": user.email,
                "attempts": 0,
            })
            try:
                redis_client = get_redis_client()
                redis_client.set(challenge_key, challenge_payload, ex=300)  # 5 minutes TTL
            except RedisError as exc:
                logger.error("Redis error creating MFA challenge: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service temporarily unavailable.",
                )

            return LoginResponse(
                mfa_required=True,
                mfa_token=mfa_token,
                access_token=None,
                refresh_token=None,
                user=None,
            )

        # Generate tokens
        access_token = create_access_token(subject=user.id)
        raw_refresh, token_hash, expires_at = create_refresh_token(subject=user.id)

        # Persist session in PostgreSQL (storing hash only)
        session = UserSession(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        db.add(session)
        db.commit()

        # Audit log successful login
        audit_service.log(
            db=db,
            action=AuditAction.LOGIN_SUCCESS,
            user_id=user.id,
            resource_type="User",
            resource_id=str(user.id),
            status=AuditStatus.SUCCESS,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        user_out = UserOut(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            account_status=user.account_status.value,
            roles=[r.name for r in user.roles],
            is_mfa_enabled=user.is_mfa_enabled,
            is_verified=user.is_verified,
            created_at=user.created_at,
        )

        return LoginResponse(
            mfa_required=False,
            mfa_token=None,
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_out,
        )

    @staticmethod
    def refresh_tokens(
        db: Session,
        refresh_token_str: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenResponse:
        """
        Validate a refresh token and perform token rotation.

        Revokes the old session and issues a new access token and refresh token pair.
        """
        try:
            payload = decode_token(refresh_token_str)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_hash = hash_token(refresh_token_str)
        session = db.query(UserSession).filter(UserSession.token_hash == token_hash).first()

        now_utc = datetime.now(timezone.utc)
        if not session or session.is_revoked or session.expires_at < now_utc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or revoked refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = db.query(User).filter(User.id == session.user_id).first()
        if not user or user.account_status != AccountStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or disabled.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Refresh Token Rotation: Revoke old session and issue new token pair
        session.is_revoked = True

        new_access_token = create_access_token(subject=user.id)
        new_raw_refresh, new_token_hash, new_expires_at = create_refresh_token(subject=user.id)

        new_session = UserSession(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            is_revoked=False,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        db.add(new_session)
        db.commit()

        # Audit log token refresh
        audit_service.log(
            db=db,
            action=AuditAction.TOKEN_REFRESH,
            user_id=user.id,
            resource_type="UserSession",
            resource_id=str(new_session.id),
            status=AuditStatus.SUCCESS,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        user_out = UserOut(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            account_status=user.account_status.value,
            roles=[r.name for r in user.roles],
            is_mfa_enabled=getattr(user, "is_mfa_enabled", False),
            is_verified=user.is_verified,
            created_at=user.created_at,
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_raw_refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_out,
        )

    @staticmethod
    def revoke_session(
        db: Session,
        refresh_token_str: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Revoke an active refresh token session on logout.
        """
        revoked_user_id = user_id
        session_id_str = None

        if refresh_token_str:
            token_hash = hash_token(refresh_token_str)
            session = db.query(UserSession).filter(UserSession.token_hash == token_hash).first()
            if session:
                session.is_revoked = True
                revoked_user_id = session.user_id
                session_id_str = str(session.id)
                db.commit()

        elif user_id:
            # If no specific refresh token provided, revoke all active sessions for this user
            sessions = (
                db.query(UserSession)
                .filter(UserSession.user_id == user_id, UserSession.is_revoked == False)  # noqa: E712
                .all()
            )
            for s in sessions:
                s.is_revoked = True
            db.commit()

        # Audit log logout event
        audit_service.log(
            db=db,
            action=AuditAction.LOGOUT,
            user_id=revoked_user_id,
            resource_type="UserSession",
            resource_id=session_id_str,
            status=AuditStatus.SUCCESS,
            ip_address=client_ip,
            user_agent=user_agent,
        )

    # =======================================================================
    # Password Reset Workflows (Phase 7)
    # =======================================================================

    @staticmethod
    def initiate_password_reset(
        db: Session,
        data: ForgotPasswordRequest,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> MessageResponse:
        """
        Initiate password recovery. Generates a secure single-use token and sends email.

        ANTI-ENUMERATION:
          - Returns a generic success message regardless of whether the account exists.
        """
        email = data.email.strip().lower()
        user = db.query(User).filter(User.email == email).first()

        generic_resp = MessageResponse(
            message="If an account exists for this email, password reset instructions have been sent."
        )

        if not user or user.account_status != AccountStatus.ACTIVE:
            # Timing/enumeration mitigation: log event and return generic response
            audit_service.log(
                db=db,
                action=AuditAction.PASSWORD_RESET_REQUESTED,
                user_id=None,
                resource_type="User",
                resource_id=email,
                status=AuditStatus.FAILURE,
                ip_address=client_ip,
                user_agent=user_agent,
            )
            return generic_resp

        # Check rate-limiting cooldown in Redis (60 seconds between reset emails)
        redis_client = get_redis_client()
        cd_key = f"pwd_reset_cd:{user.id}"
        try:
            if redis_client.get(cd_key):
                return generic_resp
        except RedisError:
            pass

        raw_token = secrets.token_urlsafe(32)
        token_digest = hash_token(raw_token)
        reset_key = f"pwd_reset:{token_digest}"
        reset_payload = json.dumps({
            "user_id": str(user.id),
            "email": user.email,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        try:
            # 15 minutes TTL
            redis_client.set(reset_key, reset_payload, ex=settings.PASSWORD_RESET_EXPIRE_MINUTES * 60)
            redis_client.set(cd_key, "1", ex=60)
        except RedisError as exc:
            logger.error("Redis error saving password reset token: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable. Please try again later.",
            )

        # Dispatch email with single-use raw token
        email_service.send_password_reset_email(user.email, user.full_name, raw_token)

        audit_service.log(
            db=db,
            action=AuditAction.PASSWORD_RESET_REQUESTED,
            user_id=user.id,
            resource_type="User",
            resource_id=str(user.id),
            status=AuditStatus.SUCCESS,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        return generic_resp

    @staticmethod
    def complete_password_reset(
        db: Session,
        data: ResetPasswordRequest,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> MessageResponse:
        """
        Validate single-use password reset token, update password hash, and revoke existing sessions.
        """
        raw_token = data.token.strip()
        token_digest = hash_token(raw_token)
        reset_key = f"pwd_reset:{token_digest}"

        redis_client = get_redis_client()
        try:
            raw_data = redis_client.get(reset_key)
        except RedisError as exc:
            logger.error("Redis error retrieving reset token: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable.",
            )

        if not raw_data:
            audit_service.log(
                db=db,
                action=AuditAction.PASSWORD_RESET_FAILED,
                user_id=None,
                resource_type="User",
                resource_id="unknown",
                status=AuditStatus.FAILURE,
                ip_address=client_ip,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token.",
            )

        try:
            token_data = json.loads(raw_data)
            user_id = uuid.UUID(token_data["user_id"])
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrupted password reset token.",
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.account_status != AccountStatus.ACTIVE:
            audit_service.log(
                db=db,
                action=AuditAction.PASSWORD_RESET_FAILED,
                user_id=user.id if user else None,
                resource_type="User",
                resource_id=str(user.id) if user else "unknown",
                status=AuditStatus.FAILURE,
                ip_address=client_ip,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is not eligible for password reset.",
            )

        # Update password hash with Argon2id
        user.password_hash = hash_password(data.new_password)

        # Invalidate all existing refresh-token sessions for this user
        sessions = db.query(UserSession).filter(UserSession.user_id == user.id).all()
        for s in sessions:
            s.is_revoked = True

        db.commit()

        # Invalidate the token from Redis immediately (single-use)
        try:
            redis_client.delete(reset_key)
        except Exception:
            pass

        audit_service.log(
            db=db,
            action=AuditAction.PASSWORD_RESET_COMPLETED,
            user_id=user.id,
            resource_type="User",
            resource_id=str(user.id),
            status=AuditStatus.SUCCESS,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        return MessageResponse(
            message="Password has been successfully reset. Please log in with your new password."
        )

    # =======================================================================
    # Multi-Factor Authentication (MFA) Workflows (Phase 7)
    # =======================================================================

    @staticmethod
    def enroll_mfa(
        db: Session,
        current_user: User,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> MfaEnrollResponse:
        """
        Initiate TOTP MFA enrollment by generating secret, URI, and one-time backup recovery codes.
        State is stored temporarily in Redis pending initial TOTP verification.
        """
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        otpauth_uri = totp.provisioning_uri(
            name=current_user.email, issuer_name=settings.MFA_ISSUER_NAME
        )
        recovery_codes = [f"{secrets.token_hex(4)}-{secrets.token_hex(4)}" for _ in range(8)]

        # Store pending enrollment in Redis (10 minutes TTL)
        redis_client = get_redis_client()
        enroll_key = f"mfa_enroll:{current_user.id}"
        enroll_payload = json.dumps({
            "secret": secret,
            "recovery_codes": recovery_codes,
        })
        try:
            redis_client.set(enroll_key, enroll_payload, ex=600)
        except RedisError as exc:
            logger.error("Redis error saving MFA enrollment: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable.",
            )

        audit_service.log(
            db=db,
            action=AuditAction.MFA_ENROLLMENT_STARTED,
            user_id=current_user.id,
            resource_type="User",
            resource_id=str(current_user.id),
            status=AuditStatus.SUCCESS,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        return MfaEnrollResponse(
            secret=secret,
            otpauth_uri=otpauth_uri,
            recovery_codes=recovery_codes,
        )

    @staticmethod
    def verify_mfa_enrollment(
        db: Session,
        current_user: User,
        data: MfaVerifyEnrollmentRequest,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> MessageResponse:
        """
        Verify initial TOTP code to confirm authenticator setup, then activate MFA for the user.
        """
        redis_client = get_redis_client()
        enroll_key = f"mfa_enroll:{current_user.id}"
        try:
            raw_data = redis_client.get(enroll_key)
        except RedisError as exc:
            logger.error("Redis error reading MFA enrollment: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable.",
            )

        if not raw_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending MFA enrollment found or enrollment expired. Please start enrollment again.",
            )

        enroll_dict = json.loads(raw_data)
        secret = enroll_dict["secret"]
        recovery_codes = enroll_dict["recovery_codes"]

        # Validate code
        if not pyotp.TOTP(secret).verify(data.code, valid_window=1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code. Please check the code in your authenticator app.",
            )

        # Hash recovery codes before persistence
        hashed_codes = [hash_token(c) for c in recovery_codes]

        current_user.is_mfa_enabled = True
        current_user.mfa_secret = encrypt_mfa_secret(secret)
        current_user.mfa_recovery_codes = hashed_codes
        db.commit()

        try:
            redis_client.delete(enroll_key)
        except Exception:
            pass

        audit_service.log(
            db=db,
            action=AuditAction.MFA_ENABLED,
            user_id=current_user.id,
            resource_type="User",
            resource_id=str(current_user.id),
            status=AuditStatus.SUCCESS,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        return MessageResponse(
            message="Two-factor authentication has been successfully enabled."
        )

    @staticmethod
    def verify_mfa_login(
        db: Session,
        data: MfaVerifyRequest,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> LoginResponse:
        """
        Complete login challenge with TOTP code or backup recovery code.
        """
        mfa_digest = hash_token(data.mfa_token)
        challenge_key = f"mfa_challenge:{mfa_digest}"

        redis_client = get_redis_client()
        try:
            raw_data = redis_client.get(challenge_key)
        except RedisError as exc:
            logger.error("Redis error reading MFA challenge: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable.",
            )

        if not raw_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA challenge expired or invalid. Please log in again.",
            )

        challenge = json.loads(raw_data)
        user_id = uuid.UUID(challenge["user_id"])
        user = db.query(User).filter(User.id == user_id).first()

        if not user or user.account_status != AccountStatus.ACTIVE or not user.is_mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account invalid for MFA authentication.",
            )

        code = data.code.strip()
        is_valid = False

        # 1. Try TOTP code validation
        plain_secret = decrypt_mfa_secret(user.mfa_secret) if user.mfa_secret else None
        if plain_secret and pyotp.TOTP(plain_secret).verify(code, valid_window=1):
            is_valid = True
        else:
            # 2. Try recovery code validation
            code_hash = hash_token(code)
            if user.mfa_recovery_codes and code_hash in user.mfa_recovery_codes:
                is_valid = True
                # Consume single-use recovery code
                updated_codes = [c for c in user.mfa_recovery_codes if c != code_hash]
                user.mfa_recovery_codes = updated_codes
                db.commit()
                audit_service.log(
                    db=db,
                    action=AuditAction.MFA_RECOVERY_USED,
                    user_id=user.id,
                    resource_type="User",
                    resource_id=str(user.id),
                    status=AuditStatus.SUCCESS,
                    ip_address=client_ip,
                    user_agent=user_agent,
                )

        if not is_valid:
            # Increment attempts and throttle
            attempts = challenge.get("attempts", 0) + 1
            challenge["attempts"] = attempts
            if attempts >= 5:
                redis_client.delete(challenge_key)
            else:
                ttl = redis_client.ttl(challenge_key)
                if ttl > 0:
                    redis_client.set(challenge_key, json.dumps(challenge), ex=ttl)

            audit_service.log(
                db=db,
                action=AuditAction.MFA_VERIFICATION_FAILED,
                user_id=user.id,
                resource_type="User",
                resource_id=str(user.id),
                status=AuditStatus.FAILURE,
                ip_address=client_ip,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid two-factor authentication code.",
            )

        # Cleanup challenge token from Redis
        try:
            redis_client.delete(challenge_key)
        except Exception:
            pass

        # Issue access token and refresh token
        access_token = create_access_token(subject=user.id)
        raw_refresh, token_hash, expires_at = create_refresh_token(subject=user.id)

        session = UserSession(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        db.add(session)
        db.commit()

        audit_service.log(
            db=db,
            action=AuditAction.LOGIN_SUCCESS,
            user_id=user.id,
            resource_type="User",
            resource_id=str(user.id),
            status=AuditStatus.SUCCESS,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        user_out = UserOut(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            account_status=user.account_status.value,
            roles=[r.name for r in user.roles],
            is_mfa_enabled=user.is_mfa_enabled,
            is_verified=user.is_verified,
            created_at=user.created_at,
        )

        return LoginResponse(
            mfa_required=False,
            mfa_token=None,
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_out,
        )

    @staticmethod
    def disable_mfa(
        db: Session,
        current_user: User,
        data: MfaDisableRequest,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> MessageResponse:
        """
        Disable MFA on user account. Requires current password verification for security.
        """
        if not current_user.is_mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Two-factor authentication is not enabled on this account.",
            )

        if not verify_password(data.password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password. Re-authentication is required to disable MFA.",
            )

        if data.code and current_user.mfa_secret:
            plain_secret = decrypt_mfa_secret(current_user.mfa_secret)
            if not pyotp.TOTP(plain_secret).verify(data.code.strip(), valid_window=1):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid TOTP code.",
                )

        current_user.is_mfa_enabled = False
        current_user.mfa_secret = None
        current_user.mfa_recovery_codes = None
        db.commit()

        audit_service.log(
            db=db,
            action=AuditAction.MFA_DISABLED,
            user_id=current_user.id,
            resource_type="User",
            resource_id=str(current_user.id),
            status=AuditStatus.SUCCESS,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        return MessageResponse(message="Two-factor authentication has been disabled.")

    @staticmethod
    def get_mfa_status(current_user: User) -> MfaStatusResponse:
        """Return non-sensitive MFA status for the authenticated user."""
        return MfaStatusResponse(enabled=bool(current_user.is_mfa_enabled))


auth_service = AuthService()
