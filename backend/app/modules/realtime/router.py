"""
Real-time WebSocket & Diagnostics HTTP Router for PustakHub.

Provides:
  - WS  /api/v1/realtime/ws     - Authenticated WebSocket endpoint with RBAC scoping
  - GET /api/v1/realtime/status - Operational diagnostics for active connections

SECURITY:
  - Public unauthenticated connections are REJECTED (HTTP 401 / WS 1008 Policy Violation).
  - Validates JWT signature, expiration, access token type, and account status from PostgreSQL.
  - Resolves dynamic DB permissions for fine-grained authorization filtering.
"""

from datetime import datetime, timezone
import json
from typing import Optional
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.logging import get_logger
from app.core.security import decode_token
from app.models.user import AccountStatus, User
from app.modules.auth.dependencies import get_current_user
from app.modules.permissions.service import permission_service
from app.modules.realtime.events import RealtimeEventType
from app.modules.realtime.manager import connection_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/realtime", tags=["realtime"])


def _authenticate_ws_token(token: str, db: Session) -> tuple[User, set[str], set[str]]:
    """
    Validate JWT access token and load user identity with dynamic roles and permissions.

    Raises:
        ValueError: If token is missing, invalid, expired, or user is inactive.
    """
    if not token:
        raise ValueError("Missing authentication token")

    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise ValueError(f"Invalid or expired access token: {exc}")

    if payload.get("type") != "access":
        raise ValueError("Invalid token type: access token required")

    sub = payload.get("sub")
    if not sub:
        raise ValueError("Malformed token: missing subject claim")

    try:
        user_uuid = uuid.UUID(sub)
    except ValueError:
        raise ValueError("Invalid user subject format")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise ValueError("User associated with token no longer exists")

    if user.account_status != AccountStatus.ACTIVE:
        raise ValueError(f"Account is not active (status: {user.account_status.value})")

    roles = {r.name.upper() for r in user.roles}
    permissions = permission_service.get_user_permissions(user, db)

    return user, roles, permissions


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="Bearer JWT access token"),
) -> None:
    """
    Primary authenticated WebSocket connection endpoint.

    Workflow:
      1. Validates JWT access token supplied in query parameters.
      2. Accepts WebSocket connection.
      3. Registers client with ConnectionManager.
      4. Handles heartbeat ping/pong messages.
      5. Gracefully disconnects on client termination or network failure.
    """
    # 1. Authenticate before accepting connection or immediately during handshake
    with SessionLocal() as db:
        try:
            # Fallback to subprotocol or header if token query param missing
            auth_token = token
            if not auth_token:
                # Check headers / sec-websocket-protocol
                auth_header = websocket.headers.get("authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    auth_token = auth_header.split(" ", 1)[1].strip()

            if not auth_token:
                logger.warning("WebSocket rejected: No authentication token supplied")
                await websocket.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Authentication required",
                )
                return

            user, roles, permissions = _authenticate_ws_token(auth_token, db)

        except ValueError as err:
            logger.warning("WebSocket authentication failed: %s", err)
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Invalid authentication token",
            )
            return
        except Exception as exc:
            logger.error("Unexpected error during WebSocket authentication: %s", exc)
            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason="Authentication processing error",
            )
            return

    # 2. Accept connection
    await websocket.accept()

    # 3. Register with connection manager
    registered = await connection_manager.connect(
        websocket=websocket,
        user_id=user.id,
        user_email=user.email,
        roles=roles,
        permissions=permissions,
    )

    if not registered:
        await websocket.close(
            code=status.WS_1013_TRY_AGAIN_LATER,
            reason="Connection limit exceeded. Please close existing tabs.",
        )
        return

    # 4. Send initial system connection confirmation
    try:
        await websocket.send_text(
            json.dumps({
                "type": RealtimeEventType.SYSTEM_NOTIFICATION.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "message": "Connected to PustakHub Realtime Stream",
                    "user_id": str(user.id),
                    "email": user.email,
                    "roles": sorted(list(roles)),
                },
            })
        )
    except Exception as exc:
        logger.debug("Failed to send initial WS greeting: %s", exc)

    # 5. Receive loop (handles ping/pong and keep-alives)
    try:
        while True:
            message_text = await websocket.receive_text()
            try:
                data = json.loads(message_text)
                msg_type = data.get("type", "").upper()

                if msg_type == "PING":
                    await websocket.send_text(
                        json.dumps({
                            "type": RealtimeEventType.PONG.value,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                    )
            except json.JSONDecodeError:
                pass  # Ignore non-JSON text payloads
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
    except Exception as exc:
        logger.debug("WebSocket connection terminated with error: %s", exc)
        await connection_manager.disconnect(websocket)


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Realtime service status",
    description="Returns operational statistics for active WebSocket connections. Requires authentication.",
)
def get_realtime_status(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Return operational connection statistics.
    """
    stats = connection_manager.get_stats()
    stats["status"] = "operational"
    stats["transport"] = "WebSocket"
    return stats
