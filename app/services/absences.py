from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import AbsenceRequest, AbsenceStatus, AbsenceType, DayType, RoleEnum, TimesheetDay, User
from app.schemas import AbsenceCreate
from app.services.access import ensure_manager_or_admin_for_target
from app.services.audit import log_event
from app.services.timesheets import get_or_create_timesheet

VACATION_LIMIT_DAYS = 14


def working_days_between(date_from, date_to) -> int:
    current = date_from
    count = 0
    while current <= date_to:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count


def _validate_absence_dates(date_from, date_to) -> None:
    if date_to < date_from:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date_to must be on or after date_from")


def _find_overlap(db: Session, user_id: int, date_from, date_to, ignore_id: int | None = None):
    query = db.query(AbsenceRequest).filter(
        AbsenceRequest.user_id == user_id,
        AbsenceRequest.status.in_([AbsenceStatus.REQUESTED, AbsenceStatus.APPROVED]),
        AbsenceRequest.date_from <= date_to,
        AbsenceRequest.date_to >= date_from,
    )
    if ignore_id is not None:
        query = query.filter(AbsenceRequest.id != ignore_id)
    return query.first()


def _approved_vacation_days_in_year(db: Session, user_id: int, year: int, ignore_id: int | None = None) -> int:
    query = db.query(AbsenceRequest).filter(
        AbsenceRequest.user_id == user_id,
        AbsenceRequest.type == AbsenceType.VACATION,
        AbsenceRequest.status == AbsenceStatus.APPROVED,
    )
    if ignore_id is not None:
        query = query.filter(AbsenceRequest.id != ignore_id)

    total = 0
    for absence in query.all():
        if absence.date_from.year == year or absence.date_to.year == year:
            total += working_days_between(absence.date_from, absence.date_to)
    return total


def _apply_absence_to_timesheets(db: Session, absence: AbsenceRequest) -> None:
    current = absence.date_from
    day_type = DayType.VACATION if absence.type == AbsenceType.VACATION else DayType.SICK
    while current <= absence.date_to:
        if current.weekday() < 5:
            timesheet = get_or_create_timesheet(db, absence.user_id, current.year, current.month)
            day = db.query(TimesheetDay).filter(TimesheetDay.timesheet_id == timesheet.id, TimesheetDay.date == current).first()
            if not day:
                day = TimesheetDay(timesheet_id=timesheet.id, date=current, hours=0, day_type=day_type)
                db.add(day)
            else:
                day.hours = 0
                day.day_type = day_type
        current += timedelta(days=1)


def _remove_absence_from_timesheets(db: Session, absence: AbsenceRequest) -> None:
    current = absence.date_from
    while current <= absence.date_to:
        if current.weekday() < 5:
            timesheet = get_or_create_timesheet(db, absence.user_id, current.year, current.month)
            day = db.query(TimesheetDay).filter(TimesheetDay.timesheet_id == timesheet.id, TimesheetDay.date == current).first()
            if day:
                day.day_type = DayType.WORK
                day.hours = 0
        current += timedelta(days=1)


def create_absence(db: Session, actor: User, payload: AbsenceCreate) -> AbsenceRequest:
    _validate_absence_dates(payload.date_from, payload.date_to)
    if _find_overlap(db, actor.id, payload.date_from, payload.date_to):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Absence request overlaps an existing requested/approved absence")

    if payload.type == AbsenceType.VACATION:
        requested_days = working_days_between(payload.date_from, payload.date_to)
        approved_days = _approved_vacation_days_in_year(db, actor.id, payload.date_from.year)
        if approved_days + requested_days > VACATION_LIMIT_DAYS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vacation limit of 14 working days exceeded")

    absence = AbsenceRequest(
        user_id=actor.id,
        type=payload.type,
        date_from=payload.date_from,
        date_to=payload.date_to,
        status=AbsenceStatus.REQUESTED,
        comment=payload.comment,
    )
    db.add(absence)
    db.flush()
    log_event(db, actor, "absence.requested", "AbsenceRequest", absence.id, {"type": absence.type, "date_from": absence.date_from, "date_to": absence.date_to})
    db.commit()
    db.refresh(absence)
    return absence


def list_absences(db: Session, actor: User) -> list[AbsenceRequest]:
    query = db.query(AbsenceRequest)
    if actor.role == RoleEnum.ADMIN:
        return query.order_by(AbsenceRequest.created_at.desc()).all()
    if actor.role == RoleEnum.MANAGER and actor.team:
        member_ids = [member.id for member in actor.team.members]
        return query.filter(AbsenceRequest.user_id.in_(member_ids)).order_by(AbsenceRequest.created_at.desc()).all()
    return query.filter(AbsenceRequest.user_id == actor.id).order_by(AbsenceRequest.created_at.desc()).all()


def approve_absence(db: Session, actor: User, absence: AbsenceRequest, comment: str | None) -> AbsenceRequest:
    ensure_manager_or_admin_for_target(actor, absence.user)
    if absence.status != AbsenceStatus.REQUESTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only requested absences can be approved")

    if absence.type == AbsenceType.VACATION:
        days = working_days_between(absence.date_from, absence.date_to)
        approved_days = _approved_vacation_days_in_year(db, absence.user_id, absence.date_from.year, ignore_id=absence.id)
        if approved_days + days > VACATION_LIMIT_DAYS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vacation limit of 14 working days exceeded")

    absence.status = AbsenceStatus.APPROVED
    absence.approver_user_id = actor.id
    if comment:
        absence.comment = (absence.comment + "\n" if absence.comment else "") + f"Decision: {comment}"
    _apply_absence_to_timesheets(db, absence)
    db.add(absence)
    log_event(db, actor, "absence.approved", "AbsenceRequest", absence.id, {"user_id": absence.user_id, "type": absence.type})
    db.commit()
    db.refresh(absence)
    return absence


def reject_absence(db: Session, actor: User, absence: AbsenceRequest, comment: str | None) -> AbsenceRequest:
    ensure_manager_or_admin_for_target(actor, absence.user)
    if absence.status != AbsenceStatus.REQUESTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only requested absences can be rejected")

    absence.status = AbsenceStatus.REJECTED
    absence.approver_user_id = actor.id
    if comment:
        absence.comment = (absence.comment + "\n" if absence.comment else "") + f"Decision: {comment}"
    db.add(absence)
    log_event(db, actor, "absence.rejected", "AbsenceRequest", absence.id, {"comment": comment})
    db.commit()
    db.refresh(absence)
    return absence


def cancel_absence(db: Session, actor: User, absence: AbsenceRequest) -> AbsenceRequest:
    if actor.role != RoleEnum.ADMIN and actor.id != absence.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner or admin can cancel this absence")
    if absence.status not in {AbsenceStatus.REQUESTED, AbsenceStatus.APPROVED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only requested or approved absences can be cancelled")

    absence.status = AbsenceStatus.CANCELLED
    _remove_absence_from_timesheets(db, absence)
    db.add(absence)
    log_event(db, actor, "absence.cancelled", "AbsenceRequest", absence.id, {"user_id": absence.user_id})
    db.commit()
    db.refresh(absence)
    return absence
