from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.camunda import service as camunda
from app.models import AbsenceRequest, AbsenceStatus, AbsenceType, DayType, RoleEnum, Timesheet, TimesheetDay, TimesheetStatus, User
from app.schemas import DayEntryCreate
from app.services.access import ensure_manager_or_admin_for_target
from app.services.audit import log_event
from app.messaging.events import AdminUnlockRequest, ApprovalDecisionMade, TimesheetSubmitted
from app.messaging.publisher import schedule_publish

MAX_MONTHLY_HOURS = 160
MAX_UNAPPROVED_SICK_DAYS = 1


def get_or_create_timesheet(db: Session, user_id: int, year: int, month: int) -> Timesheet:
    timesheet = (
        db.query(Timesheet)
        .options(joinedload(Timesheet.days))
        .filter(Timesheet.user_id == user_id, Timesheet.year == year, Timesheet.month == month)
        .first()
    )
    if not timesheet:
        timesheet = Timesheet(user_id=user_id, year=year, month=month, status=TimesheetStatus.DRAFT)
        db.add(timesheet)
        db.flush()
        db.refresh(timesheet)
    return timesheet


def ensure_timesheet_editable(timesheet: Timesheet) -> None:
    if timesheet.status in {TimesheetStatus.SUBMITTED, TimesheetStatus.APPROVED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Timesheet is locked in its current status")


def _absence_day_type(db: Session, user_id: int, entry_date) -> DayType | None:
    absence = (
        db.query(AbsenceRequest)
        .filter(
            AbsenceRequest.user_id == user_id,
            AbsenceRequest.status == AbsenceStatus.APPROVED,
            AbsenceRequest.date_from <= entry_date,
            AbsenceRequest.date_to >= entry_date,
        )
        .first()
    )
    if not absence:
        return None
    return DayType.VACATION if absence.type == AbsenceType.VACATION else DayType.SICK


def _validate_day_entries(db: Session, user: User, year: int, month: int, timesheet: Timesheet, entries: Iterable[DayEntryCreate]) -> None:
    planned_hours = {day.date: day.hours for day in timesheet.days}
    planned_day_types = {day.date: day.day_type for day in timesheet.days}
    for entry in entries:
        if entry.date.year != year or entry.date.month != month:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Entry date must belong to the selected month/year")
        if entry.day_type in {DayType.SICK, DayType.VACATION} and entry.hours != 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Absence day types must have 0 hours")

        locked_day_type = _absence_day_type(db, user.id, entry.date)
        if entry.day_type == DayType.VACATION and locked_day_type != DayType.VACATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vacation must be requested via absences, not entered directly in the timesheet",
            )
        if locked_day_type:
            if entry.hours != 0 or entry.day_type != locked_day_type:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Approved absence blocks work hour entry for that day")
            planned_day_types[entry.date] = locked_day_type
        else:
            planned_day_types[entry.date] = entry.day_type
        planned_hours[entry.date] = entry.hours

    manual_sick_days = sum(
        1
        for entry_date, day_type in planned_day_types.items()
        if day_type == DayType.SICK and _absence_day_type(db, user.id, entry_date) != DayType.SICK
    )
    if manual_sick_days > MAX_UNAPPROVED_SICK_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only one manual sick day is allowed in the timesheet. Longer sick leave must be approved as an absence.",
        )

    total = round(sum(planned_hours.values()), 2)
    if total > MAX_MONTHLY_HOURS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Monthly timesheet total cannot exceed 160 hours")


def upsert_timesheet_days(db: Session, actor: User, user: User, year: int, month: int, entries: list[DayEntryCreate]) -> Timesheet:
    timesheet = get_or_create_timesheet(db, user.id, year, month)
    ensure_timesheet_editable(timesheet)
    _validate_day_entries(db, user, year, month, timesheet, entries)

    existing = {day.date: day for day in timesheet.days}
    changes = []
    for entry in entries:
        day = existing.get(entry.date)
        actual_day_type = _absence_day_type(db, user.id, entry.date) or entry.day_type
        if not day:
            day = TimesheetDay(timesheet_id=timesheet.id, date=entry.date, hours=entry.hours, day_type=actual_day_type)
            db.add(day)
        else:
            day.hours = entry.hours
            day.day_type = actual_day_type
        changes.append({"date": entry.date.isoformat(), "hours": entry.hours, "day_type": actual_day_type})

    db.flush()
    log_event(db, actor, "timesheet.hours_changed", "Timesheet", timesheet.id, {"user_id": user.id, "changes": changes})
    db.commit()
    return (
        db.query(Timesheet)
        .options(joinedload(Timesheet.days))
        .filter(Timesheet.id == timesheet.id)
        .first()
    )


def list_timesheets(db: Session, actor: User, month: int | None = None, year: int | None = None, user_id: int | None = None) -> list[Timesheet]:
    query = db.query(Timesheet).options(joinedload(Timesheet.days), joinedload(Timesheet.user))
    if month is not None:
        query = query.filter(Timesheet.month == month)
    if year is not None:
        query = query.filter(Timesheet.year == year)

    if actor.role == RoleEnum.ADMIN:
        if user_id is not None:
            query = query.filter(Timesheet.user_id == user_id)
    elif actor.role == RoleEnum.MANAGER:
        permitted_user_ids = [member.id for member in actor.team.members] if actor.team else [actor.id]
        permitted_user_ids.append(actor.id)
        query = query.filter(Timesheet.user_id.in_(permitted_user_ids))
        if user_id is not None and user_id not in permitted_user_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized for requested user")
        if user_id is not None:
            query = query.filter(Timesheet.user_id == user_id)
    else:
        query = query.filter(Timesheet.user_id == actor.id)

    return query.order_by(Timesheet.year.desc(), Timesheet.month.desc()).all()


def submit_timesheet(db: Session, actor: User, timesheet: Timesheet) -> Timesheet:
    if actor.id != timesheet.user_id and actor.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can submit this timesheet")
    if timesheet.status not in {TimesheetStatus.DRAFT, TimesheetStatus.REJECTED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft or rejected timesheets can be submitted")

    total = round(sum(day.hours for day in timesheet.days), 2)
    if total > MAX_MONTHLY_HOURS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Monthly timesheet total cannot exceed 160 hours")

    timesheet.status = TimesheetStatus.SUBMITTED
    timesheet.submitted_at = datetime.now(timezone.utc)
    log_event(db, actor, "timesheet.submitted", "Timesheet", timesheet.id, {"total_hours": total})
    db.add(timesheet)
    db.commit()
    db.refresh(timesheet)
    schedule_publish(TimesheetSubmitted(
        actor_id=actor.id,
        timesheet_id=timesheet.id,
        user_id=timesheet.user_id,
        total_hours=total,
        year=timesheet.year,
        month=timesheet.month,
    ))
    camunda.schedule(
        camunda.start_timesheet_process(
            timesheet_id=timesheet.id,
            user_id=timesheet.user_id,
            actor_id=actor.id,
            month=timesheet.month,
            year=timesheet.year,
        )
    )
    return timesheet


def approve_timesheet(db: Session, actor: User, timesheet: Timesheet) -> Timesheet:
    if actor.id == timesheet.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot approve your own timesheet")
    ensure_manager_or_admin_for_target(actor, timesheet.user)
    if timesheet.status != TimesheetStatus.SUBMITTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only submitted timesheets can be approved")

    timesheet.status = TimesheetStatus.APPROVED
    timesheet.approved_at = datetime.now(timezone.utc)
    timesheet.approver_user_id = actor.id
    timesheet.rejection_comment = None
    db.add(timesheet)
    log_event(db, actor, "timesheet.approved", "Timesheet", timesheet.id, {"approved_for_user": timesheet.user_id})
    db.commit()
    db.refresh(timesheet)
    schedule_publish(ApprovalDecisionMade(
        actor_id=actor.id,
        entity_type="Timesheet",
        entity_id=timesheet.id,
        decision="approved",
        target_user_id=timesheet.user_id,
    ))
    camunda.schedule(
        camunda.publish_timesheet_decision(
            timesheet_id=timesheet.id,
            actor_id=actor.id,
            approved=True,
        )
    )
    return timesheet


def reject_timesheet(db: Session, actor: User, timesheet: Timesheet, comment: str | None) -> Timesheet:
    if actor.id == timesheet.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot reject your own timesheet")
    ensure_manager_or_admin_for_target(actor, timesheet.user)
    if timesheet.status != TimesheetStatus.SUBMITTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only submitted timesheets can be rejected")

    timesheet.status = TimesheetStatus.REJECTED
    timesheet.approver_user_id = actor.id
    timesheet.rejection_comment = comment or "Rejected for correction"
    db.add(timesheet)
    log_event(db, actor, "timesheet.rejected", "Timesheet", timesheet.id, {"comment": timesheet.rejection_comment})
    db.commit()
    schedule_publish(ApprovalDecisionMade(
        actor_id=actor.id,
        entity_type="Timesheet",
        entity_id=timesheet.id,
        decision="rejected",
        target_user_id=timesheet.user_id,
        comment=timesheet.rejection_comment,
    ))
    camunda.schedule(
        camunda.publish_timesheet_decision(
            timesheet_id=timesheet.id,
            actor_id=actor.id,
            approved=False,
            comment=timesheet.rejection_comment,
        )
    )
    db.refresh(timesheet)
    return timesheet


def unlock_timesheet(db: Session, actor: User, timesheet: Timesheet, reason: str) -> Timesheet:
    if actor.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can unlock timesheets")
    timesheet.status = TimesheetStatus.DRAFT
    timesheet.rejection_comment = f"Unlocked by admin: {reason}"
    timesheet.approved_at = None
    timesheet.approver_user_id = None
    db.add(timesheet)
    log_event(db, actor, "timesheet.unlocked", "Timesheet", timesheet.id, {"reason": reason})
    db.commit()
    db.refresh(timesheet)
    schedule_publish(AdminUnlockRequest(
        actor_id=actor.id,
        entity_type="Timesheet",
        entity_id=timesheet.id,
        reason=reason,
    ))
    return timesheet
