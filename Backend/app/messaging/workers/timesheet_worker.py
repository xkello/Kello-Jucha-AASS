from __future__ import annotations

import json
import logging

from aio_pika.abc import AbstractIncomingMessage

from app.messaging.workers.base import BaseWorker

logger = logging.getLogger(__name__)


class TimesheetWorker(BaseWorker):
    """
    Subscribes to timesheet.submitted events.

    Maps to: timesheet_submit.q in the architecture diagram.

    Current behaviour: structured logging. Extend this to trigger
    manager notifications, SLA deadline checks, or downstream
    integrations (e.g. payroll system).
    """

    queue_name = "timesheet_submit.q"
    routing_keys = ["timesheet.submitted"]

    async def handle(self, message: AbstractIncomingMessage) -> None:
        data = json.loads(message.body)
        logger.info(
            "[TimesheetWorker] Timesheet id=%s submitted – user=%s %.1f hrs %d/%d",
            data.get("timesheet_id"),
            data.get("user_id"),
            data.get("total_hours", 0.0),
            data.get("month"),
            data.get("year"),
        )
        # TODO: notify the user's manager, check SLA deadlines, etc.
