"""
Worker runner entrypoint.

Usage (local):
    python run_worker.py <worker_name>

Available workers:
    audit          – subscribes to all events (audit_log.q)
    notification   – subscribes to user-facing events (notification_status.q)
    timesheet      – subscribes to timesheet.submitted (timesheet_submit.q)
    absence        – subscribes to absence.requested (absence_request.q)
    approval       – subscribes to approval.decision (approval_decision.q)

In Docker, each worker runs as its own container (see docker-compose.yml).
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

WORKERS: dict[str, str] = {
    "audit":        "app.messaging.workers.audit_worker:AuditWorker",
    "notification": "app.messaging.workers.notification_worker:NotificationWorker",
    "timesheet":    "app.messaging.workers.timesheet_worker:TimesheetWorker",
    "absence":      "app.messaging.workers.absence_worker:AbsenceWorker",
    "approval":     "app.messaging.workers.approval_worker:ApprovalWorker",
}


def load_worker(spec: str):
    module_path, cls_name = spec.rsplit(":", 1)
    module = importlib.import_module(module_path)
    return getattr(module, cls_name)()


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in WORKERS:
        print("Usage: python run_worker.py <worker>")
        print(f"Available workers: {', '.join(WORKERS)}")
        sys.exit(1)

    worker_name = sys.argv[1]
    worker = load_worker(WORKERS[worker_name])
    logging.getLogger(__name__).info("Starting worker: %s", worker_name)
    asyncio.run(worker.run())
