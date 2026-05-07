from __future__ import annotations

import asyncio
import logging

import aio_pika

from app.messaging.connection import get_exchange
from app.messaging.events import DomainEvent

logger = logging.getLogger(__name__)


async def publish_event(event: DomainEvent) -> None:
    """Publish a domain event to the topic exchange (async)."""
    exchange = get_exchange()
    if exchange is None:
        logger.warning("RabbitMQ exchange not available; dropping event %s", event.event_type)
        return
    try:
        body = event.model_dump_json().encode()
        message = aio_pika.Message(
            body=body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=event.event_id,
        )
        await exchange.publish(message, routing_key=event.event_type)
        logger.debug("Published %s [%s]", event.event_type, event.event_id)
    except Exception:
        logger.exception("Failed to publish event %s", event.event_type)


def schedule_publish(event: DomainEvent) -> None:
    """
    Fire-and-forget publish from synchronous service code.

    This schedules the coroutine on the running asyncio event loop
    (which FastAPI always maintains) without blocking the caller.
    If no loop is available the event is silently dropped so the
    API response is never affected by broker unavailability.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(publish_event(event))
        else:
            logger.warning("No running event loop; cannot schedule publish for %s", event.event_type)
    except RuntimeError:
        logger.warning("No event loop available for publish of %s", event.event_type)
