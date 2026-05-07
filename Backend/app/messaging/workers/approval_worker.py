from __future__ import annotations

import json
import logging

from aio_pika.abc import AbstractIncomingMessage

from app.messaging.workers.base import BaseWorker

logger = logging.getLogger(__name__)


class ApprovalWorker(BaseWorker):
    """
    Subscribes to approval.decision events (timesheet and absence approvals/rejections).

    Maps to: approval_decision.q in the architecture diagram.

    Current behaviour: structured logging. Extend this to send decision
    notifications to the employee, update external HR records, or trigger
    payroll processing on approval.
    """

    queue_name = "approval_decision.q"
    routing_keys = ["approval.decision"]

    async def handle(self, message: AbstractIncomingMessage) -> None:
        data = json.loads(message.body)
        logger.info(
            "[ApprovalWorker] %s id=%s %s – target_user=%s actor=%s comment=%s",
            data.get("entity_type"),
            data.get("entity_id"),
            data.get("decision", "").upper(),
            data.get("target_user_id"),
            data.get("actor_id"),
            data.get("comment"),
        )
        # TODO: email the employee with the decision, update external systems, etc.
