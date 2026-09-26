"""
PustakHub — Secure Administrative CLI.

Provides a secure, interactive command to bootstrap the initial ADMIN account
outside the public registration flow.

Usage:
    python -m app.cli create-admin

SECURITY:
    - Passwords are collected via getpass (never echoed to terminal).
    - Passwords are never accepted as CLI arguments.
    - Passwords are never printed or logged.
    - Argon2id hashing uses the existing application security module.
    - Password validation matches the public registration policy exactly.
    - The ADMIN role is assigned directly (seeded by permission_service if missing).
    - If the email already exists, no changes are made and the command fails safely.
    - All operations are wrapped in a database transaction with rollback on failure.
    - An audit trail record is created without any sensitive data.
"""

import argparse
import getpass
import re
import sys
import uuid
from typing import Callable, List, Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.core.security import hash_password
from app.models.audit_log import AuditAction, AuditStatus
from app.models.role import Role
from app.models.user import AccountStatus, User
from app.modules.audit.service import audit_service
from app.modules.permissions.service import permission_service

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Password validation (reuses the exact same rules as RegisterRequest)
# ---------------------------------------------------------------------------

def _validate_password(password: str) -> List[str]:
    """
    Validate password against the application security policy.

    Returns a list of violation messages (empty list = valid).
    Uses the same rules as app.modules.auth.schemas.RegisterRequest.
    """
    errors: List[str] = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if len(password) > 128:
        errors.append("Password must be at most 128 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>\-_=+\[\]\\/~`]', password):
        errors.append("Password must contain at least one special character.")
    return errors


# ---------------------------------------------------------------------------
# Email normalization (matches app.modules.auth.schemas.RegisterRequest)
# ---------------------------------------------------------------------------

def _normalize_email(email: str) -> str:
    """Normalize email: strip whitespace and lowercase."""
    return email.strip().lower()


# ---------------------------------------------------------------------------
# create-admin core business logic & orchestration
# ---------------------------------------------------------------------------

def execute_create_admin(
    db: Session,
    full_name: str,
    email: str,
    password: str,
    password_confirm: str,
) -> User:
    """
    Create an ADMIN user account in the database.

    Raises ValueError with user-friendly error message on validation failure.
    """
    # 1. Validate full name
    full_name_clean = full_name.strip()
    if not full_name_clean or len(full_name_clean) < 2:
        raise ValueError("Full name must be at least 2 characters long.")
    if len(full_name_clean) > 255:
        raise ValueError("Full name must be at most 255 characters long.")

    # 2. Normalize and validate email
    email_clean = _normalize_email(email)
    if not email_clean or "@" not in email_clean or "." not in email_clean.split("@")[-1]:
        raise ValueError("Invalid email format.")

    # 3. Check for existing user (do not silently mutate or elevate)
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise ValueError("An account with this email already exists. No changes were made.")

    # 4. Check password match
    if password != password_confirm:
        raise ValueError("Passwords do not match.")

    # 5. Validate password policy
    validation_errors = _validate_password(password)
    if validation_errors:
        raise ValueError("\n".join(validation_errors))

    # 6. Ensure default roles & permissions are seeded
    permission_service.seed_default_roles_and_permissions(db)
    admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
    if not admin_role:
        raise RuntimeError("ADMIN role not found after seeding. Database configuration issue.")

    # 7. Hash password using Argon2id
    password_hash = hash_password(password)

    # 8. Create user directly as ACTIVE ADMIN
    user_id = uuid.uuid4()
    new_user = User(
        id=user_id,
        full_name=full_name_clean,
        email=email_clean,
        password_hash=password_hash,
        account_status=AccountStatus.ACTIVE,
        roles=[admin_role],
    )
    db.add(new_user)
    db.flush()

    # 9. Record audit event (without sensitive data)
    audit_service.log(
        db=db,
        action=AuditAction.USER_CREATED,
        user_id=user_id,
        resource_type="User",
        resource_id=f"ADMIN_BOOTSTRAP:{user_id}",
        status=AuditStatus.SUCCESS,
        ip_address="CLI",
        user_agent="PustakHub CLI create-admin",
    )

    db.commit()
    db.refresh(new_user)
    return new_user


def _create_admin(
    db: Optional[Session] = None,
    input_fn: Callable[[str], str] = input,
    getpass_fn: Callable[[str], str] = getpass.getpass,
) -> None:
    """
    Interactive bootstrap of the initial ADMIN user account.

    Steps:
        1. Collect full name, email, password (hidden), confirm password.
        2. Validate inputs & verify email does not already exist.
        3. Create User with ADMIN role, ACTIVE status, Argon2id hash.
        4. Record audit event.
        5. Commit transaction.
    """
    print()
    print("=" * 60)
    print("  PustakHub — Secure Local ADMIN Account Bootstrap")
    print("=" * 60)
    print()
    print("Enter the details for the new ADMIN account.")
    print("Password will NOT be displayed while typing.")
    print()

    session_created_here = False
    if db is None:
        db = SessionLocal()
        session_created_here = True

    try:
        full_name = input_fn("Full name: ")
        email = input_fn("Email: ")
        password = getpass_fn("Password: ")
        password_confirm = getpass_fn("Confirm password: ")

        new_user = execute_create_admin(
            db=db,
            full_name=full_name,
            email=email,
            password=password,
            password_confirm=password_confirm,
        )

        # Clear memory
        del password
        del password_confirm

        print()
        print("=" * 60)
        print("  ADMIN ACCOUNT CREATED SUCCESSFULLY")
        print("=" * 60)
        print()
        print(f"  User ID:   {new_user.id}")
        print(f"  Email:     {new_user.email}")
        print(f"  Full Name: {new_user.full_name}")
        print(f"  Role:      ADMIN")
        print(f"  Status:    ACTIVE")
        print()
        print("  Login:     http://localhost:5173/login")
        print()
        print("  Password:  [NOT DISPLAYED — entered interactively]")
        print()
        print("=" * 60)

    except (ValueError, RuntimeError) as exc:
        db.rollback()
        print(f"\n[ERROR] {exc}")
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Failed to create ADMIN account: %s", type(exc).__name__)
        print(f"\n[ERROR] Unexpected error while creating ADMIN account: {exc}")
        print("Transaction has been rolled back. No changes were made.")
        sys.exit(1)
    finally:
        if session_created_here:
            db.close()


def execute_reconcile_admin(
    db: Session,
    target_email: str = "sandipbiswal711@gmail.com",
    full_name: Optional[str] = None,
    password: Optional[str] = None,
    password_confirm: Optional[str] = None,
) -> User:
    """
    Atomically reconcile administrator role to exactly ONE target user account.

    1. Ensures ADMIN role exists.
    2. Provisions target user if nonexistent (with password validation and Argon2id hash).
       Or if existing, ensures ACTIVE status and assigns ADMIN role (preserving existing roles).
    3. Removes ADMIN role from ALL other user accounts without deleting accounts or touching other roles.
    4. Records audit events for assignment and revocations.
    5. Commits atomically in a single database transaction.
    """
    target_clean = _normalize_email(target_email)
    if not target_clean or "@" not in target_clean or "." not in target_clean.split("@")[-1]:
        raise ValueError("Invalid target email format.")

    # 1. Ensure default roles & permissions exist
    permission_service.seed_default_roles_and_permissions(db)
    admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
    if not admin_role:
        raise RuntimeError("ADMIN role not found after seeding. Database configuration issue.")

    # 2. Find or create target account
    target_user = db.query(User).filter(User.email == target_clean).first()
    if target_user:
        # Existing user: ensure ACTIVE status and assign ADMIN role
        target_user.account_status = AccountStatus.ACTIVE
        if admin_role not in target_user.roles:
            target_user.roles.append(admin_role)
            audit_service.log(
                db=db,
                action=AuditAction.ROLE_ASSIGNED,
                user_id=target_user.id,
                resource_type="UserRole",
                resource_id=f"{target_user.id}:ADMIN",
                status=AuditStatus.SUCCESS,
                ip_address="CLI",
                user_agent="PustakHub CLI reconcile-admin",
            )
    else:
        # Target user does not exist: create account
        if not full_name or len(full_name.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters long.")
        if not password or not password_confirm:
            raise ValueError("Password and password confirmation are required.")
        if password != password_confirm:
            raise ValueError("Passwords do not match.")

        validation_errors = _validate_password(password)
        if validation_errors:
            raise ValueError("\n".join(validation_errors))

        password_hash = hash_password(password)
        target_id = uuid.uuid4()
        target_user = User(
            id=target_id,
            full_name=full_name.strip(),
            email=target_clean,
            password_hash=password_hash,
            account_status=AccountStatus.ACTIVE,
            roles=[admin_role],
        )
        db.add(target_user)
        db.flush()

        audit_service.log(
            db=db,
            action=AuditAction.USER_CREATED,
            user_id=target_user.id,
            resource_type="User",
            resource_id=f"ADMIN_BOOTSTRAP:{target_user.id}",
            status=AuditStatus.SUCCESS,
            ip_address="CLI",
            user_agent="PustakHub CLI reconcile-admin",
        )
        audit_service.log(
            db=db,
            action=AuditAction.ROLE_ASSIGNED,
            user_id=target_user.id,
            resource_type="UserRole",
            resource_id=f"{target_user.id}:ADMIN",
            status=AuditStatus.SUCCESS,
            ip_address="CLI",
            user_agent="PustakHub CLI reconcile-admin",
        )

    # 3. Revoke ADMIN role from all other users
    other_admins = (
        db.query(User)
        .join(User.roles)
        .filter(Role.id == admin_role.id, User.id != target_user.id)
        .all()
    )

    for other in other_admins:
        if admin_role in other.roles:
            other.roles.remove(admin_role)
            audit_service.log(
                db=db,
                action=AuditAction.ROLE_REVOKED,
                user_id=other.id,
                resource_type="UserRole",
                resource_id=f"{other.id}:ADMIN",
                status=AuditStatus.SUCCESS,
                ip_address="CLI",
                user_agent="PustakHub CLI reconcile-admin",
            )

    db.commit()
    db.refresh(target_user)
    return target_user


def _reconcile_admin(
    db: Optional[Session] = None,
    target_email: str = "sandipbiswal711@gmail.com",
    input_fn: Callable[[str], str] = input,
    getpass_fn: Callable[[str], str] = getpass.getpass,
) -> None:
    """
    Interactive reconciliation of the single intended ADMIN account.
    """
    print()
    print("=" * 60)
    print("  PustakHub — Administrator Account Reconciliation")
    print("=" * 60)
    print()

    session_created_here = False
    if db is None:
        db = SessionLocal()
        session_created_here = True

    try:
        clean_email = _normalize_email(target_email)
        existing = db.query(User).filter(User.email == clean_email).first()

        full_name = None
        password = None
        password_confirm = None

        if existing:
            print(f"Target account '{clean_email}' found (ID: {existing.id}, Status: {existing.account_status.value}).")
            print("Existing user record, password, and non-ADMIN roles will be preserved.")
        else:
            print(f"Target account '{clean_email}' not found. Please provide details to create it:")
            full_name = input_fn("Full name: ")
            password = getpass_fn("Password: ")
            password_confirm = getpass_fn("Confirm password: ")

        target_user = execute_reconcile_admin(
            db=db,
            target_email=clean_email,
            full_name=full_name,
            password=password,
            password_confirm=password_confirm,
        )

        if password:
            del password
        if password_confirm:
            del password_confirm

        print()
        print("=" * 60)
        print("  ADMIN RECONCILIATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print()
        print(f"  Target ADMIN ID:     {target_user.id}")
        print(f"  Target ADMIN Email:  {target_user.email}")
        print(f"  Target ADMIN Name:   {target_user.full_name}")
        print(f"  Target ADMIN Status: {target_user.account_status.value}")
        print(f"  Target ADMIN Roles:  {', '.join([r.name for r in target_user.roles])}")
        print()
        print("  All other users have had the ADMIN role safely revoked.")
        print("  All existing non-ADMIN accounts and roles remain preserved.")
        print("=" * 60)

    except (ValueError, RuntimeError) as exc:
        db.rollback()
        print(f"\n[ERROR] {exc}")
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Failed to reconcile ADMIN account: %s", type(exc).__name__)
        print(f"\n[ERROR] Unexpected error during reconciliation: {exc}")
        print("Transaction has been rolled back. No changes were made.")
        sys.exit(1)
    finally:
        if session_created_here:
            db.close()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate command."""
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="PustakHub administrative command-line interface.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # create-admin subcommand
    subparsers.add_parser(
        "create-admin",
        help="Bootstrap the initial ADMIN user account interactively.",
    )

    # reconcile-admin subcommand
    reconcile_parser = subparsers.add_parser(
        "reconcile-admin",
        help="Reconcile exactly one ADMIN account and revoke ADMIN from others.",
    )
    reconcile_parser.add_argument(
        "--email",
        default="sandipbiswal711@gmail.com",
        help="Target administrator email address (default: sandipbiswal711@gmail.com)",
    )

    args = parser.parse_args()

    if args.command == "create-admin":
        _create_admin()
    elif args.command == "reconcile-admin":
        _reconcile_admin(target_email=args.email)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

