from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import RoleEnum, Timesheet, User
from app.schemas import DayEntryCreate, DayEntryUpdate, TimesheetActionRequest, TimesheetRead, UnlockRequest
from app.services.timesheets import approve_timesheet, list_timesheets, reject_timesheet, submit_timesheet, unlock_timesheet, upsert_timesheet_days

router = APIRouter(prefix="/timesheets", tags=["timesheets"])


@router.get("", response_model=list[TimesheetRead])
def get_timesheets(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    user_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_timesheets(db, current_user, month=month, year=year, user_id=user_id)


@router.post("/{year}/{month}/days", response_model=TimesheetRead)
def create_or_update_days(
    year: int,
    month: int,
    entries: list[DayEntryCreate],
    user_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if month < 1 or month > 12:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month")
    target_user = current_user if user_id is None else db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if current_user.role != RoleEnum.ADMIN and current_user.id != target_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner or admin can edit timesheets")
    return upsert_timesheet_days(db, current_user, target_user, year, month, entries)


@router.patch("/{timesheet_id}/days/{entry_date}", response_model=TimesheetRead)
def update_single_day(
    timesheet_id: int,
    entry_date: date,
    payload: DayEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    timesheet = db.get(Timesheet, timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timesheet not found")
    target_user = db.get(User, timesheet.user_id)
    if current_user.role != RoleEnum.ADMIN and current_user.id != timesheet.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner or admin can edit timesheets")
    entry = DayEntryCreate(date=entry_date, hours=payload.hours)
    return upsert_timesheet_days(db, current_user, target_user, timesheet.year, timesheet.month, [entry])


@router.post("/{timesheet_id}/submit", response_model=TimesheetRead)
def submit_endpoint(timesheet_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    timesheet = db.get(Timesheet, timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timesheet not found")
    return submit_timesheet(db, current_user, timesheet)


@router.post("/{timesheet_id}/approve", response_model=TimesheetRead)
def approve_endpoint(timesheet_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    timesheet = db.get(Timesheet, timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timesheet not found")
    return approve_timesheet(db, current_user, timesheet)


@router.post("/{timesheet_id}/reject", response_model=TimesheetRead)
def reject_endpoint(
    timesheet_id: int,
    payload: TimesheetActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    timesheet = db.get(Timesheet, timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timesheet not found")
    return reject_timesheet(db, current_user, timesheet, payload.comment)


@router.post("/{timesheet_id}/unlock", response_model=TimesheetRead)
def unlock_endpoint(
    timesheet_id: int,
    payload: UnlockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    timesheet = db.get(Timesheet, timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timesheet not found")
    return unlock_timesheet(db, current_user, timesheet, payload.reason)
