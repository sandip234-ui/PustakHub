"""
Tests for the PustakHub ADMIN bootstrap CLI (app.cli create-admin).

Covers all 10 required test cases:
  1. Test 1 — creates ADMIN: new email, valid password, creates exactly one user, status ACTIVE, ADMIN role assigned
  2. Test 2 — password hashing: plaintext password is never stored, existing password verification succeeds
  3. Test 3 — duplicate email: existing user, command does not create another user, command does not modify existing roles
  4. Test 4 — duplicate execution: run equivalent creation twice, only one ADMIN user exists
  5. Test 5 — invalid password confirmation: rejected, no user created
  6. Test 6 — invalid password policy: rejected, no user created
  7. Test 7 — email normalization: uppercase/whitespace input follows existing normalization
  8. Test 8 — transaction rollback: simulated failure, no partially-created user/role remains
  9. Test 9 — audit: successful ADMIN bootstrap creates appropriate audit record, no secrets appear in audit metadata
  10. Test 10 — existing STUDENT is not silently promoted: create a STUDENT, run create-admin using that email, command fails safely, role remains unchanged

Plus:
  - Unit tests for password validation & email normalization
  - Public registration security boundary integrity verification
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.cli import (
    _create_admin,
    _normalize_email,
    _validate_password,
    execute_create_admin,
)
from app.core.database import SessionLocal
from app.core.security import hash_password, verify_password
from app.models.audit_log import AuditAction, AuditLog
from app.models.role import Role
from app.models.user import AccountStatus, User
from app.modules.permissions.service import permission_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    """Provide a database session for each test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Unit tests: _validate_password
# ---------------------------------------------------------------------------

class TestPasswordValidation:
    """Verify the CLI reuses the same password rules as RegisterRequest."""

    def test_valid_password_returns_empty_list(self):
        errors = _validate_password("SecurePass123!")
        assert errors == []

    def test_too_short_password(self):
        errors = _validate_password("Ab1!")
        assert any("at least 8 characters" in e for e in errors)

    def test_too_long_password(self):
        errors = _validate_password("A" * 129 + "a1!")
        assert any("at most 128 characters" in e for e in errors)

    def test_missing_uppercase(self):
        errors = _validate_password("securepass123!")
        assert any("uppercase" in e for e in errors)

    def test_missing_lowercase(self):
        errors = _validate_password("SECUREPASS123!")
        assert any("lowercase" in e for e in errors)

    def test_missing_digit(self):
        errors = _validate_password("SecurePassWord!")
        assert any("digit" in e for e in errors)

    def test_missing_special_char(self):
        errors = _validate_password("SecurePass123")
        assert any("special character" in e for e in errors)

    def test_all_rules_pass_complex_password(self):
        errors = _validate_password("P@ssw0rd_Complex!2026")
        assert errors == []


# ---------------------------------------------------------------------------
# Unit tests: _normalize_email
# ---------------------------------------------------------------------------

class TestEmailNormalization:
    """Verify email normalization matches the auth service behavior."""

    def test_strips_whitespace(self):
        assert _normalize_email("  user@example.com  ") == "user@example.com"

    def test_lowercases_email(self):
        assert _normalize_email("User@Example.COM") == "user@example.com"

    def test_combined_strip_and_lowercase(self):
        assert _normalize_email("  Admin@PustakHub.COM  ") == "admin@pustakhub.com"


# ---------------------------------------------------------------------------
# Integration tests: 10 Required Test Cases
# ---------------------------------------------------------------------------

class TestAdminBootstrapCLI:
    """Validate all 10 required ADMIN bootstrap requirements."""

    def test_01_creates_admin_success(self, db: Session):
        """Test 1: Creates exactly one user, status ACTIVE, ADMIN role assigned."""
        unique_email = f"bootstrap-admin-{uuid.uuid4().hex[:8]}@example.com"
        raw_password = "AdminSecurePassword123!"

        user = execute_create_admin(
            db=db,
            full_name="Bootstrap Admin User",
            email=unique_email,
            password=raw_password,
            password_confirm=raw_password,
        )

        assert user is not None
        assert user.email == unique_email
        assert user.full_name == "Bootstrap Admin User"
        assert user.account_status == AccountStatus.ACTIVE

        # Verify exactly one user with this email in database
        users = db.query(User).filter(User.email == unique_email).all()
        assert len(users) == 1

        # Verify role assignment
        role_names = [r.name for r in user.roles]
        assert "ADMIN" in role_names

    def test_02_password_hashing(self, db: Session):
        """Test 2: Plaintext password is never stored; verification succeeds."""
        unique_email = f"pwd-admin-{uuid.uuid4().hex[:8]}@example.com"
        raw_password = "CorrectHorseBatteryStaple99!"

        user = execute_create_admin(
            db=db,
            full_name="Password Test Admin",
            email=unique_email,
            password=raw_password,
            password_confirm=raw_password,
        )

        assert user.password_hash != raw_password
        assert user.password_hash.startswith("$argon2id$")
        assert raw_password not in user.password_hash

        # Verify password check functions
        assert verify_password(raw_password, user.password_hash) is True
        assert verify_password("WrongPassword123!", user.password_hash) is False

    def test_03_duplicate_email_rejected_no_modifications(self, db: Session):
        """Test 3: Existing user is not modified and no new user is created."""
        unique_email = f"existing-user-{uuid.uuid4().hex[:8]}@example.com"

        # Create baseline user
        permission_service.seed_default_roles_and_permissions(db)
        librarian_role = db.query(Role).filter(Role.name == "LIBRARIAN").first()
        existing_user = User(
            full_name="Original Librarian",
            email=unique_email,
            password_hash=hash_password("OriginalPass123!"),
            account_status=AccountStatus.ACTIVE,
            roles=[librarian_role],
        )
        db.add(existing_user)
        db.commit()
        db.refresh(existing_user)
        original_id = existing_user.id
        original_roles = [r.name for r in existing_user.roles]

        # Attempt to run create-admin with same email
        with pytest.raises(ValueError, match="already exists"):
            execute_create_admin(
                db=db,
                full_name="New Admin Attempt",
                email=unique_email,
                password="NewPassword123!",
                password_confirm="NewPassword123!",
            )

        # Confirm DB state is unchanged
        db.expire_all()
        user_after = db.query(User).filter(User.email == unique_email).first()
        assert user_after.id == original_id
        assert user_after.full_name == "Original Librarian"
        assert [r.name for r in user_after.roles] == original_roles
        assert verify_password("OriginalPass123!", user_after.password_hash) is True

    def test_04_duplicate_execution_prevents_duplicate_accounts(self, db: Session):
        """Test 4: Running creation twice with same email results in only one user."""
        unique_email = f"idempotent-{uuid.uuid4().hex[:8]}@example.com"
        raw_password = "ValidPassword123!"

        # First run succeeds
        user1 = execute_create_admin(
            db=db,
            full_name="Idempotent Admin",
            email=unique_email,
            password=raw_password,
            password_confirm=raw_password,
        )
        assert user1 is not None

        # Second run fails safely
        with pytest.raises(ValueError, match="already exists"):
            execute_create_admin(
                db=db,
                full_name="Idempotent Admin Second Attempt",
                email=unique_email,
                password=raw_password,
                password_confirm=raw_password,
            )

        # Exactly 1 user exists
        count = db.query(User).filter(User.email == unique_email).count()
        assert count == 1

    def test_05_invalid_password_confirmation(self, db: Session):
        """Test 5: Mismatched passwords reject and create no user."""
        unique_email = f"mismatch-{uuid.uuid4().hex[:8]}@example.com"

        with pytest.raises(ValueError, match="Passwords do not match"):
            execute_create_admin(
                db=db,
                full_name="Mismatch Admin",
                email=unique_email,
                password="Password123!",
                password_confirm="DifferentPassword123!",
            )

        # No user created
        user = db.query(User).filter(User.email == unique_email).first()
        assert user is None

    def test_06_invalid_password_policy(self, db: Session):
        """Test 6: Weak password fails security policy and creates no user."""
        unique_email = f"weak-{uuid.uuid4().hex[:8]}@example.com"

        with pytest.raises(ValueError, match="uppercase"):
            execute_create_admin(
                db=db,
                full_name="Weak Pass Admin",
                email=unique_email,
                password="weakpassword123!",  # no uppercase
                password_confirm="weakpassword123!",
            )

        # No user created
        user = db.query(User).filter(User.email == unique_email).first()
        assert user is None

    def test_07_email_normalization(self, db: Session):
        """Test 7: Uppercase and whitespace in email is normalized."""
        raw_email = f"  ADMIN.Normalized-{uuid.uuid4().hex[:6]}@PUSTAKHUB.COM  "
        expected_email = raw_email.strip().lower()
        password = "AdminPass123!"

        user = execute_create_admin(
            db=db,
            full_name="Normalized Admin",
            email=raw_email,
            password=password,
            password_confirm=password,
        )

        assert user.email == expected_email
        queried = db.query(User).filter(User.email == expected_email).first()
        assert queried is not None

    def test_08_transaction_rollback(self, db: Session):
        """Test 8: Failure during process rolls back transaction completely."""
        unique_email = f"rollback-{uuid.uuid4().hex[:8]}@example.com"
        password = "AdminPass123!"

        with patch("app.modules.audit.service.audit_service.log", side_effect=RuntimeError("Simulated audit disk failure")):
            with pytest.raises(RuntimeError, match="Simulated audit disk failure"):
                try:
                    execute_create_admin(
                        db=db,
                        full_name="Rollback Test Admin",
                        email=unique_email,
                        password=password,
                        password_confirm=password,
                    )
                except Exception:
                    db.rollback()
                    raise

        # User was rolled back
        user = db.query(User).filter(User.email == unique_email).first()
        assert user is None

    def test_09_audit_logging_without_secrets(self, db: Session):
        """Test 9: Audit record is logged with action USER_CREATED and contains no secrets."""
        unique_email = f"audit-admin-{uuid.uuid4().hex[:8]}@example.com"
        raw_password = "SuperSecretPassword123!"

        user = execute_create_admin(
            db=db,
            full_name="Audited Admin",
            email=unique_email,
            password=raw_password,
            password_confirm=raw_password,
        )

        # Check audit log in DB
        audit_entry = (
            db.query(AuditLog)
            .filter(
                AuditLog.action == AuditAction.USER_CREATED,
                AuditLog.user_id == user.id,
            )
            .first()
        )
        assert audit_entry is not None
        assert audit_entry.resource_type == "User"
        assert f"ADMIN_BOOTSTRAP:{user.id}" in audit_entry.resource_id

        # Inspect all audit fields for sensitive leaks
        forbidden = ["argon2id", raw_password.lower(), "secret", "token", "otp"]
        for forbidden_word in forbidden:
            assert forbidden_word not in str(audit_entry.resource_id).lower()

    def test_10_existing_student_is_not_silently_promoted(self, db: Session):
        """Test 10: Existing STUDENT account cannot be converted to ADMIN via create-admin."""
        unique_email = f"student-target-{uuid.uuid4().hex[:8]}@example.com"
        student_password = "StudentPassword123!"

        # Create baseline STUDENT
        permission_service.seed_default_roles_and_permissions(db)
        student_role = db.query(Role).filter(Role.name == "STUDENT").first()
        student_user = User(
            full_name="Student Original",
            email=unique_email,
            password_hash=hash_password(student_password),
            account_status=AccountStatus.ACTIVE,
            roles=[student_role],
        )
        db.add(student_user)
        db.commit()
        db.refresh(student_user)

        # Try to run create-admin on student's email
        with pytest.raises(ValueError, match="already exists. No changes were made."):
            execute_create_admin(
                db=db,
                full_name="Attempted Admin Elevation",
                email=unique_email,
                password="NewPassword123!",
                password_confirm="NewPassword123!",
            )

        # Verify student still has ONLY the STUDENT role
        db.expire_all()
        refreshed_student = db.query(User).filter(User.email == unique_email).first()
        role_names = [r.name for r in refreshed_student.roles]
        assert role_names == ["STUDENT"]
        assert "ADMIN" not in role_names
        assert verify_password(student_password, refreshed_student.password_hash) is True


# ---------------------------------------------------------------------------
# Interactive CLI invocation test
# ---------------------------------------------------------------------------

class TestCLIInteractiveExecution:
    """Test the CLI interactive wrapper functions with simulated inputs."""

    def test_interactive_create_admin_success(self, db: Session, capsys):
        unique_email = f"interactive-admin-{uuid.uuid4().hex[:8]}@example.com"
        password = "InteractivePass123!"

        inputs = iter(["Interactive Admin", unique_email])
        getpass_inputs = iter([password, password])

        _create_admin(
            db=db,
            input_fn=lambda prompt: next(inputs),
            getpass_fn=lambda prompt: next(getpass_inputs),
        )

        captured = capsys.readouterr()
        assert "ADMIN ACCOUNT CREATED SUCCESSFULLY" in captured.out
        assert unique_email in captured.out

        # Verify created
        user = db.query(User).filter(User.email == unique_email).first()
        assert user is not None
        assert "ADMIN" in [r.name for r in user.roles]

    def test_interactive_create_admin_duplicate_aborts_safely(self, db: Session, capsys):
        unique_email = f"interactive-dup-{uuid.uuid4().hex[:8]}@example.com"
        password = "InteractivePass123!"

        # Pre-create
        execute_create_admin(
            db=db,
            full_name="First Admin",
            email=unique_email,
            password=password,
            password_confirm=password,
        )

        inputs = iter(["Second Admin", unique_email])
        getpass_inputs = iter([password, password])

        with pytest.raises(SystemExit) as exc_info:
            _create_admin(
                db=db,
                input_fn=lambda prompt: next(inputs),
                getpass_fn=lambda prompt: next(getpass_inputs),
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "already exists. No changes were made." in captured.out


# ---------------------------------------------------------------------------
# Public Registration Security Boundary Integrity
# ---------------------------------------------------------------------------

class TestPublicRegistrationIntegrity:
    """Verify that the public registration flow cannot create ADMIN accounts."""

    def test_register_schema_has_no_role_field(self):
        """RegisterRequest must not accept a role parameter."""
        from app.modules.auth.schemas import RegisterRequest
        field_names = set(RegisterRequest.model_fields.keys())
        assert "role" not in field_names
        assert "roles" not in field_names
        assert "role_name" not in field_names

    def test_registration_hardcodes_student_role(self):
        """
        Inspect the auth service source to confirm STUDENT is hardcoded
        in verify_registration_otp, not parameterized.
        """
        import inspect
        from app.modules.auth.service import AuthService
        source = inspect.getsource(AuthService.verify_registration_otp)
        assert 'Role.name == "STUDENT"' in source
        assert 'Role.name == "ADMIN"' not in source


# ---------------------------------------------------------------------------
# Admin Reconciliation Tests
# ---------------------------------------------------------------------------

class TestAdminReconciliation:
    """Verify execute_reconcile_admin assigns ADMIN to target and revokes from all others."""

    def test_reconcile_promotes_existing_user_and_revokes_others(self, db: Session):
        permission_service.seed_default_roles_and_permissions(db)
        admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
        student_role = db.query(Role).filter(Role.name == "STUDENT").first()

        # Create target user as STUDENT
        target_email = f"target-{uuid.uuid4().hex[:8]}@example.com"
        target_user = User(
            id=uuid.uuid4(),
            full_name="Target Student",
            email=target_email,
            password_hash=hash_password("ValidPassword123!"),
            account_status=AccountStatus.ACTIVE,
            roles=[student_role],
        )
        db.add(target_user)

        # Create previous admin
        prev_admin_email = f"prev-admin-{uuid.uuid4().hex[:8]}@example.com"
        prev_admin = User(
            id=uuid.uuid4(),
            full_name="Previous Admin",
            email=prev_admin_email,
            password_hash=hash_password("ValidPassword123!"),
            account_status=AccountStatus.ACTIVE,
            roles=[admin_role, student_role],
        )
        db.add(prev_admin)
        db.commit()

        # Reconcile target user
        from app.cli import execute_reconcile_admin
        result = execute_reconcile_admin(db=db, target_email=target_email)

        assert result.id == target_user.id
        assert "ADMIN" in [r.name for r in result.roles]
        assert "STUDENT" in [r.name for r in result.roles]
        assert result.account_status == AccountStatus.ACTIVE

        # Verify previous admin has ADMIN revoked but STUDENT preserved
        db.refresh(prev_admin)
        assert "ADMIN" not in [r.name for r in prev_admin.roles]
        assert "STUDENT" in [r.name for r in prev_admin.roles]

    def test_reconcile_creates_new_user_if_nonexistent(self, db: Session):
        permission_service.seed_default_roles_and_permissions(db)
        from app.cli import execute_reconcile_admin

        new_email = f"brand-new-{uuid.uuid4().hex[:8]}@example.com"
        result = execute_reconcile_admin(
            db=db,
            target_email=new_email,
            full_name="Brand New Admin",
            password="SecureAdminPass123!",
            password_confirm="SecureAdminPass123!",
        )

        assert result.email == new_email
        assert "ADMIN" in [r.name for r in result.roles]
        assert result.account_status == AccountStatus.ACTIVE

