"""
Connection Manager for WebSockets in PustakHub.

Manages authenticated active client WebSocket connections, enforces connection limits,
and distributes real-time events based on Role-Based Access Control (RBAC) and user scoping.

SECURITY:
  - Connections are strictly mapped to authenticated user IDs and evaluated permissions.
  - Subscriptions are server-governed; clients cannot arbitrarily subscribe to other users' private events.
  - Sensitive events (audit logs, IAM mutations, member circulation records) are delivered ONLY to authorized callers.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional, Set
import uuid

from fastapi import WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.modules.permissions.constants import AppPermission
from app.modules.realtime.events import (
    AUDIT_EVENTS,
    CATALOG_EVENTS,
    CIRCULATION_EVENTS,
    IAM_EVENTS,
    RealtimeEvent,
)

logger = get_logger(__name__)

# Bounded connection limits to protect against resource exhaustion
MAX_TOTAL_CONNECTIONS = 1000
MAX_CONNECTIONS_PER_USER = 10


@dataclass
class ConnectionInfo:
    """Metadata associated with an active authenticated WebSocket connection."""

    websocket: WebSocket
    user_id: uuid.UUID
    user_email: str
    roles: Set[str]
    permissions: Set[str]
    connected_at: datetime


class ConnectionManager:
    """
    Thread-safe connection manager for WebSocket clients.
    """

    def __init__(self) -> None:
        self._active_connections: Dict[WebSocket, ConnectionInfo] = {}
        self._user_connections: Dict[uuid.UUID, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        user_id: uuid.UUID,
        user_email: str,
        roles: Set[str],
        permissions: Set[str],
    ) -> bool:
        """
        Register a new authenticated WebSocket connection.

        Returns True if registered successfully, False if limits exceeded.
        """
        async with self._lock:
            if len(self._active_connections) >= MAX_TOTAL_CONNECTIONS:
                logger.warning(
                    "WebSocket connection rejected: Global connection limit reached (%d)",
                    MAX_TOTAL_CONNECTIONS,
                )
                return False

            user_conns = self._user_connections.setdefault(user_id, set())
            if len(user_conns) >= MAX_CONNECTIONS_PER_USER:
                logger.warning(
                    "WebSocket connection rejected: User %s (%s) exceeded connection limit (%d)",
                    user_email,
                    user_id,
                    MAX_CONNECTIONS_PER_USER,
                )
                return False

            info = ConnectionInfo(
                websocket=websocket,
                user_id=user_id,
                user_email=user_email,
                roles={r.upper() for r in roles},
                permissions={p.lower() for p in permissions},
                connected_at=datetime.now(timezone.utc),
            )
            self._active_connections[websocket] = info
            user_conns.add(websocket)

            logger.info(
                "WebSocket client connected: user=%s (%s), roles=%s, active_total=%d",
                user_email,
                user_id,
                info.roles,
                len(self._active_connections),
            )
            return True

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Unregister an active WebSocket connection.
        """
        async with self._lock:
            info = self._active_connections.pop(websocket, None)
            if info:
                user_conns = self._user_connections.get(info.user_id)
                if user_conns:
                    user_conns.discard(websocket)
                    if not user_conns:
                        self._user_connections.pop(info.user_id, None)

                logger.info(
                    "WebSocket client disconnected: user=%s (%s), active_total=%d",
                    info.user_email,
                    info.user_id,
                    len(self._active_connections),
                )

    def is_authorized_for_event(
        self, info: ConnectionInfo, event: RealtimeEvent
    ) -> bool:
        """
        Evaluate whether a connected user is authorized to receive a specific real-time event.

        RULES:
          1. AUDIT_EVENTS:
             - Caller must possess `audit_log:view` permission or `ADMIN` role.
          2. IAM_EVENTS (User lifecycle, role changes):
             - Caller must possess `user:view` permission or `ADMIN` role.
             - OR caller is the target user affected (`event.target_user_id == str(info.user_id)`).
          3. CIRCULATION_EVENTS (Issue, return, fines):
             - If `target_user_id` matches connection: caller is the borrower/patron -> ALLOW.
             - If caller holds staff circulation permissions (`book:issue`, `book:return`, `ADMIN`, `LIBRARIAN`) -> ALLOW.
             - Otherwise -> DENY (student A cannot receive student B's circulation/fine events).
          4. CATALOG_EVENTS (Books, copies, categories):
             - All authenticated users are authorized to observe catalog updates.
        """
        is_admin = "ADMIN" in info.roles
        is_librarian = "LIBRARIAN" in info.roles

        # 1. Audit logs
        if event.type in AUDIT_EVENTS:
            return (
                is_admin
                or AppPermission.AUDIT_LOG_VIEW.value in info.permissions
                or "audit_log:view" in info.permissions
            )

        # 2. IAM events
        if event.type in IAM_EVENTS:
            if is_admin or AppPermission.USER_VIEW.value in info.permissions:
                return True
            # Allow target user to receive their own status/role update
            if event.target_user_id and str(info.user_id) == str(event.target_user_id):
                return True
            return False

        # 3. Circulation & Fines events
        if event.type in CIRCULATION_EVENTS:
            # Check if this connection is the target patron
            if event.target_user_id and str(info.user_id) == str(event.target_user_id):
                return True
            # Check if this connection is library staff
            if (
                is_admin
                or is_librarian
                or AppPermission.BOOK_ISSUE.value in info.permissions
                or AppPermission.BOOK_RETURN.value in info.permissions
            ):
                return True
            return False

        # 4. Catalog events
        if event.type in CATALOG_EVENTS:
            return True

        # Default system events (e.g. system notification)
        return True

    async def broadcast_event(self, event: RealtimeEvent) -> int:
        """
        Broadcast an event to all authorized connected WebSocket clients.

        Returns count of clients delivered to.
        """
        payload_text = json.dumps(
            event.model_dump(mode="json"),
            default=str,
        )

        stale_sockets: List[WebSocket] = []
        delivered_count = 0

        # Snapshot active connections to minimize lock retention
        async with self._lock:
            connections_snapshot = list(self._active_connections.items())

        for ws, info in connections_snapshot:
            if not self.is_authorized_for_event(info, event):
                continue

            try:
                await ws.send_text(payload_text)
                delivered_count += 1
            except (WebSocketDisconnect, ConnectionResetError, RuntimeError) as exc:
                logger.debug(
                    "Error sending event to user %s (%s): %s",
                    info.user_email,
                    info.user_id,
                    exc,
                )
                stale_sockets.append(ws)
            except Exception as exc:
                logger.warning(
                    "Unexpected error delivering WebSocket event to %s: %s",
                    info.user_email,
                    exc,
                )
                stale_sockets.append(ws)

        # Cleanup any disconnected or broken sockets
        if stale_sockets:
            for ws in stale_sockets:
                await self.disconnect(ws)

        return delivered_count

    async def send_to_user(self, user_id: uuid.UUID, event: RealtimeEvent) -> int:
        """
        Send an event directly to all active connections for a specific user ID.
        """
        payload_text = json.dumps(
            event.model_dump(mode="json"),
            default=str,
        )

        stale_sockets: List[WebSocket] = []
        delivered_count = 0

        async with self._lock:
            user_sockets = list(self._user_connections.get(user_id, set()))

        for ws in user_sockets:
            try:
                await ws.send_text(payload_text)
                delivered_count += 1
            except Exception:
                stale_sockets.append(ws)

        if stale_sockets:
            for ws in stale_sockets:
                await self.disconnect(ws)

        return delivered_count

    def get_stats(self) -> Dict[str, Any]:
        """Return operational connection metrics."""
        return {
            "active_connections": len(self._active_connections),
            "unique_users": len(self._user_connections),
            "max_total_limit": MAX_TOTAL_CONNECTIONS,
            "max_per_user_limit": MAX_CONNECTIONS_PER_USER,
        }


# Global singleton ConnectionManager instance
connection_manager = ConnectionManager()
