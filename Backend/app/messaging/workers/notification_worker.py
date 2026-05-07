from __future__ import annotations

import json
import logging

from aio_pika.abc import AbstractIncomingMessage

from app.messaging.workers.base import BaseWorker

logger = logging.getLogger(__name__)


class NotificationWorker(BaseWorker):
    """
    Subscribes to the key user-facing events and dispatches notifications.

    Maps to: notification_status.q in the architecture diagram.

    Current behaviour: structured logging. Extend this to send emails,
    push notifications, Slack messages, etc. using any notification
    provider (SendGrid, Twilio, Firebase, etc.).
    """

    queue_name = "notification_status.q"
    routing_keys = [
        "timesheet.submitted",
        "absence.requested",
        "approval.decision",
        "admin.unlock",
    ]

    async def handle(self, message: AbstractIncomingMessage) -> None:
        data = json.loads(message.body)
        event_type = data.get("event_type", "unknown")
        logger.info(
            "[NotificationWorker] Dispatching notification for %s event_id=%s actor=%s",
            event_type,
            data.get("event_id"),
            data.get("actor_id"),
        )
        # TODO: route to email/push/Slack based on event_type and user preferences.
