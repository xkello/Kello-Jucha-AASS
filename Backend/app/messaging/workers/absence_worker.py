from __future__ import annotations

import json
import logging

from aio_pika.abc import AbstractIncomingMessage

from app.messaging.workers.base import BaseWorker

logger = logging.getLogger(__name__)


class AbsenceWorker(BaseWorker):
    """
    Subscribes to absence.requested events.

    Maps to: absence_request.q in the architecture diagram.

    Current behaviour: structured logging. Extend this to notify the
    relevant manager, trigger quota pre-checks, or sync to an HR system.
    """

    queue_name = "absence_request.q"
    routing_keys = ["absence.requested"]

    async def handle(self, message: AbstractIncomingMessage) -> None:
        data = json.loads(message.body)
        logger.info(
            "[AbsenceWorker] Absence id=%s requested – user=%s type=%s (%s → %s)",
            data.get("absence_id"),
            data.get("user_id"),
            data.get("absence_type"),
            data.get("date_from"),
            data.get("date_to"),
        )
        # TODO: notify manager, validate quota limits asynchronously, etc.
