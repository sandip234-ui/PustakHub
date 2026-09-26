"""
Redis Pub/Sub Subscriber for Distributed Real-time Updates in PustakHub.

Enables multi-worker deployment synchronization: when an event is published
on one worker process, it is published to Redis Pub/Sub so that other worker
processes can broadcast it to their locally connected WebSocket clients.
"""

import asyncio
from datetime import datetime, timezone
import json
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import get_logger
from app.modules.realtime.events import RealtimeEvent
from app.modules.realtime.manager import connection_manager
from app.modules.realtime.publisher import REDIS_PUBSUB_CHANNEL

logger = get_logger(__name__)

_subscriber_task: Optional[asyncio.Task] = None
_stop_event = asyncio.Event()


async def _listen_redis_channel() -> None:
    """Async listener loop connecting to Redis Pub/Sub."""
    while not _stop_event.is_set():
        try:
            redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
            client = aioredis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
            )
            pubsub = client.pubsub()
            await pubsub.subscribe(REDIS_PUBSUB_CHANNEL)
            logger.info("Subscribed to Redis Pub/Sub channel: %s", REDIS_PUBSUB_CHANNEL)

            while not _stop_event.is_set():
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message.get("type") == "message":
                    raw_data = message.get("data")
                    if raw_data and isinstance(raw_data, str):
                        try:
                            event_dict = json.loads(raw_data)
                            event = RealtimeEvent(**event_dict)
                            # Broadcast to local connections
                            await connection_manager.broadcast_event(event)
                        except Exception as parse_err:
                            logger.debug("Error parsing Redis Pub/Sub message: %s", parse_err)

                await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            break
        except Exception as exc:
            if not _stop_event.is_set():
                logger.debug("Redis Pub/Sub subscriber connection retry: %s", exc)
                await asyncio.sleep(5)  # Backoff before reconnect


def start_redis_subscriber() -> None:
    """Start the background Redis subscriber task during app startup."""
    global _subscriber_task, _stop_event
    _stop_event.clear()
    try:
        loop = asyncio.get_running_loop()
        _subscriber_task = loop.create_task(_listen_redis_channel())
    except RuntimeError:
        pass


def stop_redis_subscriber() -> None:
    """Stop the background Redis subscriber task during app shutdown."""
    global _subscriber_task, _stop_event
    _stop_event.set()
    if _subscriber_task:
        _subscriber_task.cancel()
        _subscriber_task = None
