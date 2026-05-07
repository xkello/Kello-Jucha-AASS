from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import RoleEnum, Team, User
from app.schemas import AddMemberRequest, TeamCreate, TeamRead, TeamUpdate
from app.services.teams import add_member_to_team, create_team, remove_member_from_team, update_team

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[TeamRead])
def list_teams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == RoleEnum.ADMIN:
        return db.query(Team).order_by(Team.id).all()
    if current_user.team_id is None:
        return []
    team = db.get(Team, current_user.team_id)
    return [team] if team else []


@router.post("", response_model=TeamRead)
def create_team_endpoint(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    return create_team(db, current_user, payload)


@router.patch("/{team_id}", response_model=TeamRead)
def update_team_endpoint(
    team_id: int,
    payload: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return update_team(db, current_user, team, payload)


@router.post("/{team_id}/members", response_model=TeamRead)
def add_member_endpoint(
    team_id: int,
    payload: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    team = db.get(Team, team_id)
    user = db.get(User, payload.user_id)
    if not team or not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team or user not found")
    return add_member_to_team(db, current_user, team, user)


@router.delete("/{team_id}/members/{user_id}", response_model=TeamRead)
def remove_member_endpoint(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    team = db.get(Team, team_id)
    user = db.get(User, user_id)
    if not team or not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team or user not found")
    return remove_member_from_team(db, current_user, team, user)
