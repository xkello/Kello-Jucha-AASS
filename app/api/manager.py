from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import require_roles
from app.models import AbsenceRequest, AbsenceStatus, RoleEnum, Timesheet, TimesheetStatus, User

router = APIRouter(prefix="/manager", tags=["manager"])


@router.get("/pending-timesheets")
def pending_timesheets(db: Session = Depends(get_db), current_user: User = Depends(require_roles(RoleEnum.MANAGER, RoleEnum.ADMIN))):
    query = db.query(Timesheet).options(joinedload(Timesheet.user)).filter(Timesheet.status == TimesheetStatus.SUBMITTED)
    if current_user.role == RoleEnum.MANAGER:
        query = query.join(User, User.id == Timesheet.user_id).filter(User.team_id == current_user.team_id, User.id != current_user.id)
    items = query.all()
    return [{"id": item.id, "user_id": item.user_id, "user_name": item.user.name, "month": item.month, "year": item.year} for item in items]


@router.get("/pending-absences")
def pending_absences(db: Session = Depends(get_db), current_user: User = Depends(require_roles(RoleEnum.MANAGER, RoleEnum.ADMIN))):
    query = db.query(AbsenceRequest).options(joinedload(AbsenceRequest.user)).filter(AbsenceRequest.status == AbsenceStatus.REQUESTED)
    if current_user.role == RoleEnum.MANAGER:
        query = query.join(User, User.id == AbsenceRequest.user_id).filter(User.team_id == current_user.team_id, User.id != current_user.id)
    items = query.all()
    return [{"id": item.id, "user_id": item.user_id, "user_name": item.user.name, "type": item.type, "date_from": item.date_from, "date_to": item.date_to} for item in items]


@router.get("/team-overview")
def team_overview(db: Session = Depends(get_db), current_user: User = Depends(require_roles(RoleEnum.MANAGER, RoleEnum.ADMIN))):
    if current_user.role == RoleEnum.ADMIN:
        total_users = db.query(User).count()
        return {
            "scope": "all_teams",
            "total_users": total_users,
            "pending_timesheets": db.query(Timesheet).filter(Timesheet.status == TimesheetStatus.SUBMITTED).count(),
            "pending_absences": db.query(AbsenceRequest).filter(AbsenceRequest.status == AbsenceStatus.REQUESTED).count(),
        }

    member_ids = [member.id for member in current_user.team.members] if current_user.team else []
    return {
        "scope": "own_team",
        "team_id": current_user.team_id,
        "member_count": len(member_ids),
        "pending_timesheets": db.query(Timesheet).filter(Timesheet.user_id.in_(member_ids), Timesheet.status == TimesheetStatus.SUBMITTED).count() if member_ids else 0,
        "pending_absences": db.query(AbsenceRequest).filter(AbsenceRequest.user_id.in_(member_ids), AbsenceRequest.status == AbsenceStatus.REQUESTED).count() if member_ids else 0,
    }
