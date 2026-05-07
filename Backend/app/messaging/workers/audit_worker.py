from __future__ import annotations

import json
import logging

from aio_pika.abc import AbstractIncomingMessage

from app.messaging.workers.base import BaseWorker

logger = logging.getLogger(__name__)


class AuditWorker(BaseWorker):
    """
    Subscribes to ALL events (wildcard `#`).

    Maps to: audit_log.q in the architecture diagram.

    Current behaviour: structured logging of every domain event for
    observability. Extend this to write to a dedicated event-store
    or stream to an external log aggregator (e.g. ELK, Loki).

    Note: synchronous audit DB writes already happen inside the service
    layer via log_event(). This worker is an *additional* async channel
    for cross-cutting audit concerns.
    """

    queue_name = "audit_log.q"
    routing_keys = ["#"]  # wildcard – receives every event on the exchange

    async def handle(self, message: AbstractIncomingMessage) -> None:
        data = json.loads(message.body)
        logger.info(
            "[AuditWorker] event_type=%s event_id=%s actor_id=%s occurred_at=%s",
            data.get("event_type"),
            data.get("event_id"),
            data.get("actor_id"),
            data.get("occurred_at"),
        )
