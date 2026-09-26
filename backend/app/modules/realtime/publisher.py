"""
Real-time Event Publisher for PustakHub.

Provides non-blocking, fail-safe publishing of domain and security events
to local WebSocket connections and Redis Pub/Sub.

SAFETY GUARANTEES:
  - Non-blocking: failures in event publishing or Redis disconnection NEVER crash REST operations.
  - Sanitization: filters out sensitive fields (tokens, passwords, hashes, secrets).
  - Dual-dispatch: delivers to local in-process connections and broadcasts to Redis Pub/Sub.
"""

import asyncio
from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional, Union
import uuid

from app.core.logging import get_logger
from app.core.redis import get_redis_client
from app.modules.realtime.events import RealtimeEvent, RealtimeEventType
from app.modules.realtime.manager import connection_manager

logger = get_logger(__name__)

REDIS_PUBSUB_CHANNEL = "pustakhub:realtime:events"

_FORBIDDEN_KEYWORD_SUBSTRINGS = (
    "password",
    "argon2id",
    "secret",
    "token",
    "otp",
    "recovery",
    "authorization",
    "key",
)


def _sanitize_data_payload(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Ensure the data payload contains no sensitive credentials or raw secrets.
    """
    if not data:
        return data

    sanitized: Dict[str, Any] = {}
    for k, v in data.items():
        k_lower = str(k).lower()
        if any(bad in k_lower for bad in _FORBIDDEN_KEYWORD_SUBSTRINGS):
            sanitized[k] = "[REDACTED]"
            continue

        if isinstance(v, str) and (
            "$argon2id$" in v.lower() or "bearer " in v.lower() or len(v) > 500
        ):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, (dict, list, int, float, bool, str)) or v is None:
            sanitized[k] = v
        else:
            sanitized[k] = str(v)

    return sanitized


async def _dispatch_event_async(event: RealtimeEvent) -> None:
    """Internal async dispatch to local connections and Redis Pub/Sub."""
    try:
        # 1. Local WebSocket broadcast
        await connection_manager.broadcast_event(event)

        # 2. Redis Pub/Sub distribution (for multi-worker sync)
        try:
            redis_client = get_redis_client()
            if redis_client:
                event_json = json.dumps(event.model_dump(mode="json"), default=str)
                redis_client.publish(REDIS_PUBSUB_CHANNEL, event_json)
        except Exception as redis_exc:
            logger.debug("Redis Pub/Sub publish skipped or failed: %s", redis_exc)

    except Exception as exc:
        logger.warning("Error during real-time event dispatch: %s", exc)


def publish_realtime_event(
    event_type: RealtimeEventType,
    resource_type: Optional[str] = None,
    resource_id: Optional[Union[str, uuid.UUID]] = None,
    actor_user_id: Optional[Union[str, uuid.UUID]] = None,
    target_user_id: Optional[Union[str, uuid.UUID]] = None,
    data: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> Optional[RealtimeEvent]:
    """
    Publish a real-time event safely from any synchronous or asynchronous context.

    Parameters:
        event_type: Canonical RealtimeEventType.
        resource_type: Affected entity name ('Book', 'BorrowRecord', 'User', etc.).
        resource_id: Non-sensitive resource ID or string PK.
        actor_user_id: Actor UUID string.
        target_user_id: Target user UUID string (for private scoped events).
        data: Optional summary payload (strictly sanitized).
        request_id: Correlation/Request ID.

    Returns:
        The instantiated RealtimeEvent object, or None if creation failed.
    """
    try:
        sanitized_data = _sanitize_data_payload(data)

        event = RealtimeEvent(
            type=event_type,
            timestamp=datetime.now(timezone.utc),
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            actor_user_id=str(actor_user_id) if actor_user_id is not None else None,
            target_user_id=str(target_user_id) if target_user_id is not None else None,
            data=sanitized_data,
            request_id=request_id,
        )

        # Attempt to schedule in current event loop if running
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(_dispatch_event_async(event))
            else:
                asyncio.run(_dispatch_event_async(event))
        except RuntimeError:
            # No running loop (e.g. in certain test fixtures or threads)
            try:
                asyncio.run(_dispatch_event_async(event))
            except Exception as sync_exc:
                logger.debug("Async dispatch in isolated loop: %s", sync_exc)

        return event

    except Exception as exc:
        logger.warning("Failed to publish real-time event [%s]: %s", event_type, exc)
        return None
