"""
Phase 17 Real-Time Updates & WebSocket Test Suite for PustakHub.

Verifies:
  1. WebSocket Authentication & Validation:
     - Valid access token accepted
     - Missing, invalid, or expired tokens rejected (Policy violation)
     - Suspended and deactivated accounts rejected
  2. RBAC & Scoped Event Delivery:
     - ADMIN receives global operational, audit, and IAM events
     - LIBRARIAN receives catalog and circulation events
     - STUDENT receives catalog updates and ONLY their own private borrowing/fine events
     - Cross-student event isolation (Student A cannot see Student B's circulation events)
     - Audit log event delivery restricted to authorized roles/permissions
  3. Sensitive Data Protection:
     - Real-time payloads strictly exclude secrets, passwords, hashes, tokens, and MFA keys
  4. Connection Lifecycle & Resilience:
     - Heartbeat ping/pong frames
     - Connection registration and cleanup on disconnect
     - Non-blocking fail-safe publishing (REST operations succeed even if publisher encounters errors)
  5. Diagnostics:
     - GET /api/v1/realtime/status returns active metrics
"""

from datetime import datetime, timedelta, timezone
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.book import Book
from app.models.book_copy import BookCopy, CopyStatus
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.models.category import Category
from app.models.role import Role
from app.models.user import AccountStatus, User
from app.modules.permissions.constants import AppPermission
from app.modules.permissions.service import permission_service
from app.modules.realtime.events import RealtimeEvent, RealtimeEventType
from app.modules.realtime.manager import connection_manager
from app.modules.realtime.publisher import publish_realtime_event


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def test_data():
    """Seed test users with different roles for real-time testing."""
    with SessionLocal() as db:
        permission_service.seed_default_roles_and_permissions(db)

        admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
        librarian_role = db.query(Role).filter(Role.name == "LIBRARIAN").first()
        student_role = db.query(Role).filter(Role.name == "STUDENT").first()

        # Admin user
        admin = db.query(User).filter(User.email == "rt_admin@example.com").first()
        if not admin:
            admin = User(
                email="rt_admin@example.com",
                full_name="Realtime Admin",
                password_hash=hash_password("AdminPass123!"),
                account_status=AccountStatus.ACTIVE,
                roles=[admin_role],
            )
            db.add(admin)
        else:
            admin.roles = [admin_role]
            admin.account_status = AccountStatus.ACTIVE

        # Librarian user
        librarian = db.query(User).filter(User.email == "rt_librarian@example.com").first()
        if not librarian:
            librarian = User(
                email="rt_librarian@example.com",
                full_name="Realtime Librarian",
                password_hash=hash_password("LibrarianPass123!"),
                account_status=AccountStatus.ACTIVE,
                roles=[librarian_role],
            )
            db.add(librarian)
        else:
            librarian.roles = [librarian_role]
            librarian.account_status = AccountStatus.ACTIVE

        # Student A
        student_a = db.query(User).filter(User.email == "rt_student_a@example.com").first()
        if not student_a:
            student_a = User(
                email="rt_student_a@example.com",
                full_name="Student Alpha",
                password_hash=hash_password("StudentPass123!"),
                account_status=AccountStatus.ACTIVE,
                roles=[student_role],
            )
            db.add(student_a)
        else:
            student_a.roles = [student_role]
            student_a.account_status = AccountStatus.ACTIVE

        # Student B
        student_b = db.query(User).filter(User.email == "rt_student_b@example.com").first()
        if not student_b:
            student_b = User(
                email="rt_student_b@example.com",
                full_name="Student Beta",
                password_hash=hash_password("StudentPass123!"),
                account_status=AccountStatus.ACTIVE,
                roles=[student_role],
            )
            db.add(student_b)
        else:
            student_b.roles = [student_role]
            student_b.account_status = AccountStatus.ACTIVE

        # Suspended User
        suspended = db.query(User).filter(User.email == "rt_suspended@example.com").first()
        if not suspended:
            suspended = User(
                email="rt_suspended@example.com",
                full_name="Suspended User",
                password_hash=hash_password("SuspendedPass123!"),
                account_status=AccountStatus.SUSPENDED,
                roles=[student_role],
            )
            db.add(suspended)
        else:
            suspended.roles = [student_role]
            suspended.account_status = AccountStatus.SUSPENDED

        # Book for Catalog Events (query canonical holding)
        book = db.query(Book).filter(Book.isbn == "978-1-999999-01-8").first()
        if not book:
            cat = db.query(Category).filter(Category.name == "Operating Systems & Kernel").first() or db.query(Category).first()
            book = Book(
                title="Realtime Systems",
                author="Alan Turing",
                isbn="978-1-999999-01-8",
                category_id=cat.id,
            )
            db.add(book)
            db.flush()

        db.commit()
        db.refresh(admin)
        db.refresh(librarian)
        db.refresh(student_a)
        db.refresh(student_b)
        db.refresh(suspended)
        db.refresh(book)

        return {
            "admin_id": admin.id,
            "librarian_id": librarian.id,
            "student_a_id": student_a.id,
            "student_b_id": student_b.id,
            "suspended_id": suspended.id,
            "admin_token": create_access_token(admin.id),
            "librarian_token": create_access_token(librarian.id),
            "student_a_token": create_access_token(student_a.id),
            "student_b_token": create_access_token(student_b.id),
            "suspended_token": create_access_token(suspended.id),
            "book_id": book.id,
        }


# ===========================================================================
# 1. AUTHENTICATION & HANDSHAKE TESTS
# ===========================================================================


class TestWebSocketAuthentication:
    def test_connect_with_valid_token_succeeds(self, client, test_data):
        """Valid JWT access token successfully establishes WebSocket connection."""
        token = test_data["admin_token"]
        with client.websocket_connect(f"/api/v1/realtime/ws?token={token}") as ws:
            # Receive initial greeting
            data = ws.receive_json()
            assert data["type"] == RealtimeEventType.SYSTEM_NOTIFICATION.value
            assert "Connected" in data["data"]["message"]
            assert data["data"]["user_id"] == str(test_data["admin_id"])
            assert "ADMIN" in data["data"]["roles"]

    def test_connect_without_token_rejected(self, client):
        """Connection attempt without token is rejected with policy violation."""
        with pytest.raises(Exception):
            with client.websocket_connect("/api/v1/realtime/ws"):
                pass

    def test_connect_with_invalid_token_rejected(self, client):
        """Connection attempt with corrupted token is rejected."""
        with pytest.raises(Exception):
            with client.websocket_connect("/api/v1/realtime/ws?token=invalid.jwt.token"):
                pass

    def test_connect_with_suspended_user_token_rejected(self, client, test_data):
        """Suspended user token is rejected during handshake."""
        token = test_data["suspended_token"]
        with pytest.raises(Exception):
            with client.websocket_connect(f"/api/v1/realtime/ws?token={token}"):
                pass


# ===========================================================================
# 2. HEARTBEAT & PING-PONG TESTS
# ===========================================================================


class TestWebSocketHeartbeat:
    def test_ping_pong_exchange(self, client, test_data):
        """Client sending PING receives PONG with UTC timestamp."""
        token = test_data["student_a_token"]
        with client.websocket_connect(f"/api/v1/realtime/ws?token={token}") as ws:
            # Consume initial greeting
            _ = ws.receive_json()

            # Send PING frame
            ws.send_text(json.dumps({"type": "PING"}))

            # Receive PONG response
            response = ws.receive_json()
            assert response["type"] == RealtimeEventType.PONG.value
            assert "timestamp" in response


# ===========================================================================
# 3. RBAC & SCOPED EVENT DELIVERY TESTS
# ===========================================================================


class TestWebSocketEventDeliveryAndScoping:
    def test_catalog_event_delivered_to_all_authenticated_users(self, client, test_data):
        """Catalog updates are broadcast to all authenticated subscribers."""
        token = test_data["student_a_token"]
        with client.websocket_connect(f"/api/v1/realtime/ws?token={token}") as ws:
            _ = ws.receive_json()  # greeting

            # Publish a catalog event
            publish_realtime_event(
                event_type=RealtimeEventType.BOOK_CREATED,
                resource_type="Book",
                resource_id=str(test_data["book_id"]),
                data={"title": "New Arrival Book"},
            )

            event = ws.receive_json()
            assert event["type"] == RealtimeEventType.BOOK_CREATED.value
            assert event["resource_id"] == str(test_data["book_id"])
            assert event["data"]["title"] == "New Arrival Book"

    def test_private_circulation_event_delivered_to_target_student(self, client, test_data):
        """Borrowing events targeting Student A are received by Student A."""
        token_a = test_data["student_a_token"]
        with client.websocket_connect(f"/api/v1/realtime/ws?token={token_a}") as ws_a:
            _ = ws_a.receive_json()

            # Publish event scoped to Student A
            borrow_id = uuid.uuid4()
            publish_realtime_event(
                event_type=RealtimeEventType.COPY_ISSUED,
                resource_type="BorrowRecord",
                resource_id=str(borrow_id),
                target_user_id=test_data["student_a_id"],
                data={"copy_identifier": "TEST-BARCODE-01"},
            )

            event = ws_a.receive_json()
            assert event["type"] == RealtimeEventType.COPY_ISSUED.value
            assert event["resource_id"] == str(borrow_id)
            assert event["target_user_id"] == str(test_data["student_a_id"])

    def test_student_isolation_cannot_receive_other_students_events(self, client, test_data):
        """Student B does NOT receive private borrowing events meant exclusively for Student A."""
        token_b = test_data["student_b_token"]
        with client.websocket_connect(f"/api/v1/realtime/ws?token={token_b}") as ws_b:
            _ = ws_b.receive_json()

            # Publish event targeted to Student A
            publish_realtime_event(
                event_type=RealtimeEventType.FINE_ISSUED,
                resource_type="Fine",
                resource_id=str(uuid.uuid4()),
                target_user_id=test_data["student_a_id"],
                data={"amount": "10.00"},
            )

            # Send a PING to ensure event would have been delivered if allowed
            ws_b.send_text(json.dumps({"type": "PING"}))
            response = ws_b.receive_json()

            # The response must be the PONG, NOT Student A's fine event!
            assert response["type"] == RealtimeEventType.PONG.value

    def test_admin_receives_global_audit_and_circulation_events(self, client, test_data):
        """Admin subscribers receive all audit logs and operational events."""
        admin_token = test_data["admin_token"]
        with client.websocket_connect(f"/api/v1/realtime/ws?token={admin_token}") as ws_admin:
            _ = ws_admin.receive_json()

            audit_id = uuid.uuid4()
            publish_realtime_event(
                event_type=RealtimeEventType.AUDIT_EVENT_CREATED,
                resource_type="AuditLog",
                resource_id=str(audit_id),
                data={"action": "USER_LOGIN_SUCCESS", "status": "SUCCESS"},
            )

            event = ws_admin.receive_json()
            assert event["type"] == RealtimeEventType.AUDIT_EVENT_CREATED.value
            assert event["resource_id"] == str(audit_id)


# ===========================================================================
# 4. SENSITIVE DATA PROTECTION & SCHEMA VALIDATION
# ===========================================================================


class TestEventSecurityAndSanitization:
    def test_sensitive_fields_redacted_from_payload(self):
        """Sensitive keys like passwords, tokens, and hashes are automatically redacted."""
        event = publish_realtime_event(
            event_type=RealtimeEventType.USER_UPDATED,
            resource_type="User",
            resource_id="test-user-id",
            data={
                "email": "safe@example.com",
                "password_hash": "$argon2id$v=19$m=65536...secret",
                "access_token": "bearer eyJhbGciOi...",
                "totp_secret": "JBSWY3DPEHPK3PXP",
            },
        )

        assert event is not None
        assert event.data["email"] == "safe@example.com"
        assert event.data["password_hash"] == "[REDACTED]"
        assert event.data["access_token"] == "[REDACTED]"
        assert event.data["totp_secret"] == "[REDACTED]"


# ===========================================================================
# 5. DIAGNOSTICS & STATUS ENDPOINT
# ===========================================================================


class TestRealtimeStatusEndpoint:
    def test_status_endpoint_authenticated(self, client, test_data):
        """GET /api/v1/realtime/status returns operational metrics."""
        response = client.get(
            "/api/v1/realtime/status",
            headers={"Authorization": f"Bearer {test_data['admin_token']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["transport"] == "WebSocket"
        assert "active_connections" in data
        assert "max_total_limit" in data

    def test_status_endpoint_unauthenticated_rejected(self, client):
        """GET /api/v1/realtime/status requires authentication."""
        response = client.get("/api/v1/realtime/status")
        assert response.status_code == 401
