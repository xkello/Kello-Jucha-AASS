from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import AbsenceRequest, User
from app.schemas import AbsenceCreate, AbsenceRead, TimesheetActionRequest
from app.services.absences import approve_absence, cancel_absence, create_absence, list_absences, reject_absence

router = APIRouter(prefix="/absences", tags=["absences"])


@router.get("", response_model=list[AbsenceRead])
def get_absences(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return list_absences(db, current_user)


@router.post("", response_model=AbsenceRead)
def create_absence_endpoint(
    payload: AbsenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_absence(db, current_user, payload)


@router.post("/{absence_id}/approve", response_model=AbsenceRead)
def approve_absence_endpoint(
    absence_id: int,
    payload: TimesheetActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    absence = db.get(AbsenceRequest, absence_id)
    if not absence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Absence request not found")
    return approve_absence(db, current_user, absence, payload.comment)


@router.post("/{absence_id}/reject", response_model=AbsenceRead)
def reject_absence_endpoint(
    absence_id: int,
    payload: TimesheetActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    absence = db.get(AbsenceRequest, absence_id)
    if not absence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Absence request not found")
    return reject_absence(db, current_user, absence, payload.comment)


@router.post("/{absence_id}/cancel", response_model=AbsenceRead)
def cancel_absence_endpoint(
    absence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    absence = db.get(AbsenceRequest, absence_id)
    if not absence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Absence request not found")
    return cancel_absence(db, current_user, absence)
