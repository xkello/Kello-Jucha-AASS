from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from pyzeebe import ZeebeWorker, create_insecure_channel

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Timesheet, TimesheetStatus, User
from app.services.audit import log_event

logger = logging.getLogger(__name__)

def _get_timesheet_and_user(db, timesheet_id: int) -> tuple[Timesheet | None, User | None]:
    timesheet = db.get(Timesheet, timesheet_id)
    user = db.get(User, timesheet.user_id) if timesheet else None
    return timesheet, user


def validate_timesheet(timesheetId: int, userId: int, month: int, year: int) -> dict:
    db = SessionLocal()
    try:
        timesheet = db.get(Timesheet, timesheetId)
        if not timesheet:
            return {"isValid": False, "validationComment": "Timesheet not found"}
        if timesheet.user_id != userId or timesheet.month != month or timesheet.year != year:
            return {"isValid": False, "validationComment": "Submitted process data does not match the stored timesheet"}
        if timesheet.status != TimesheetStatus.SUBMITTED:
            return {"isValid": False, "validationComment": "Timesheet is not in submitted state"}

        total_hours = round(sum(day.hours for day in timesheet.days), 2)
        if total_hours > 160:
            return {"isValid": False, "validationComment": "Monthly timesheet total cannot exceed 160 hours"}

        user = db.get(User, userId)
        if not user or not user.active:
            return {"isValid": False, "validationComment": "Timesheet owner is missing or inactive"}

        return {"isValid": True, "validationComment": None}
    finally:
        db.close()


def assign_manager(timesheetId: int, userId: int) -> dict:
    db = SessionLocal()
    try:
        user = db.get(User, userId)
        manager_id = None
        if user and user.team:
            manager_id = user.team.manager_user_id
        logger.info("[CamundaWorker] assign-manager timesheet=%s manager=%s", timesheetId, manager_id)
        return {"managerId": manager_id}
    finally:
        db.close()


def return_timesheet(timesheetId: int, validationComment: str | None = None) -> dict:
    db = SessionLocal()
    try:
        timesheet, user = _get_timesheet_and_user(db, timesheetId)
        if not timesheet:
            return {}
        if timesheet.status == TimesheetStatus.SUBMITTED:
            timesheet.status = TimesheetStatus.REJECTED
            timesheet.rejection_comment = validationComment or "Returned for correction by workflow validation"
            timesheet.approver_user_id = None
            timesheet.approved_at = None
            db.add(timesheet)
            log_event(
                db,
                None,
                "camunda.timesheet.returned",
                "Timesheet",
                timesheet.id,
                {"comment": timesheet.rejection_comment, "user_id": user.id if user else None},
            )
            db.commit()
        return {}
    finally:
        db.close()


def notify_employee_correction(timesheetId: int, userId: int, validationComment: str | None = None) -> dict:
    logger.info(
        "[CamundaWorker] notify-employee-correction timesheet=%s user=%s comment=%s",
        timesheetId,
        userId,
        validationComment,
    )
    return {}


def set_timesheet_approved(timesheetId: int, actorId: int | None = None) -> dict:
    db = SessionLocal()
    try:
        timesheet, user = _get_timesheet_and_user(db, timesheetId)
        if not timesheet:
            return {}
        if timesheet.status != TimesheetStatus.APPROVED:
            timesheet.status = TimesheetStatus.APPROVED
            timesheet.approved_at = datetime.now(timezone.utc)
            timesheet.approver_user_id = actorId
            timesheet.rejection_comment = None
            db.add(timesheet)
            log_event(
                db,
                None,
                "camunda.timesheet.approved",
                "Timesheet",
                timesheet.id,
                {"user_id": user.id if user else None, "actor_id": actorId},
            )
            db.commit()
        return {}
    finally:
        db.close()


def archive_timesheet(timesheetId: int) -> dict:
    logger.info("[CamundaWorker] archive-timesheet timesheet=%s", timesheetId)
    return {}


def send_approval_confirmation(timesheetId: int, userId: int) -> dict:
    logger.info("[CamundaWorker] send-approval-confirmation timesheet=%s user=%s", timesheetId, userId)
    return {}


def set_timesheet_rejected(timesheetId: int, actorId: int | None = None, comment: str | None = None) -> dict:
    db = SessionLocal()
    try:
        timesheet, user = _get_timesheet_and_user(db, timesheetId)
        if not timesheet:
            return {}
        if timesheet.status != TimesheetStatus.REJECTED:
            timesheet.status = TimesheetStatus.REJECTED
            timesheet.approver_user_id = actorId
            timesheet.rejection_comment = comment or "Rejected by manager decision"
            db.add(timesheet)
            log_event(
                db,
                None,
                "camunda.timesheet.rejected",
                "Timesheet",
                timesheet.id,
                {"user_id": user.id if user else None, "actor_id": actorId, "comment": timesheet.rejection_comment},
            )
            db.commit()
        return {}
    finally:
        db.close()


def notify_employee_rejection(timesheetId: int, userId: int, comment: str | None = None) -> dict:
    logger.info(
        "[CamundaWorker] notify-employee-rejection timesheet=%s user=%s comment=%s",
        timesheetId,
        userId,
        comment,
    )
    return {}


def create_worker() -> ZeebeWorker:
    channel = create_insecure_channel(grpc_address=settings.zeebe_address)
    worker = ZeebeWorker(channel)
    worker.task(task_type="validate-timesheet")(validate_timesheet)
    worker.task(task_type="assign-manager")(assign_manager)
    worker.task(task_type="return-timesheet")(return_timesheet)
    worker.task(task_type="notify-employee-correction")(notify_employee_correction)
    worker.task(task_type="set-timesheet-approved")(set_timesheet_approved)
    worker.task(task_type="archive-timesheet")(archive_timesheet)
    worker.task(task_type="send-approval-confirmation")(send_approval_confirmation)
    worker.task(task_type="set-timesheet-rejected")(set_timesheet_rejected)
    worker.task(task_type="notify-employee-rejection")(notify_employee_rejection)
    return worker


async def run() -> None:
    logger.info("Starting Camunda worker on %s", settings.zeebe_address)
    delay_seconds = 5
    while True:
        try:
            worker = create_worker()
            await worker.work()
            return
        except Exception as exc:  # pragma: no cover - integration resilience
            logger.warning(
                "Camunda worker connection failed, retrying in %ss: %s",
                delay_seconds,
                exc,
                exc_info=True,
            )
            await asyncio.sleep(delay_seconds)
