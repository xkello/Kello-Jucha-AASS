from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import RoleEnum, Team, User
from app.schemas import TeamCreate, TeamUpdate
from app.services.audit import log_event


def _validate_manager(db: Session, manager_user_id: int | None) -> User | None:
    if manager_user_id is None:
        return None
    manager = db.get(User, manager_user_id)
    if not manager:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manager user not found")
    if manager.role not in {RoleEnum.MANAGER, RoleEnum.ADMIN}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned manager must have MANAGER or ADMIN role")
    return manager


def create_team(db: Session, actor: User, payload: TeamCreate) -> Team:
    if db.query(Team).filter(Team.name == payload.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team name already exists")

    team = Team(name=payload.name, active=True)
    db.add(team)
    db.flush()

    manager = _validate_manager(db, payload.manager_user_id)
    if manager:
        manager.team_id = team.id
        team.manager_user_id = manager.id

    log_event(db, actor, "team.created", "Team", team.id, {"name": team.name, "manager_user_id": team.manager_user_id})
    db.commit()
    db.refresh(team)
    return team


def update_team(db: Session, actor: User, team: Team, payload: TeamUpdate) -> Team:
    before = {"name": team.name, "manager_user_id": team.manager_user_id, "active": team.active}

    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        existing = db.query(Team).filter(Team.name == data["name"], Team.id != team.id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team name already exists")
        team.name = data["name"]

    if "manager_user_id" in data:
        manager = _validate_manager(db, data["manager_user_id"])
        team.manager_user_id = manager.id if manager else None
        if manager:
            manager.team_id = team.id

    if "active" in data:
        team.active = data["active"]

    db.add(team)
    log_event(db, actor, "team.updated", "Team", team.id, {"before": before, "after": data})
    db.commit()
    db.refresh(team)
    return team


def add_member_to_team(db: Session, actor: User, team: Team, user: User) -> Team:
    user.team_id = team.id
    db.add(user)
    log_event(db, actor, "team.member_added", "Team", team.id, {"user_id": user.id})
    db.commit()
    db.refresh(team)
    return team


def remove_member_from_team(db: Session, actor: User, team: Team, user: User) -> Team:
    if team.manager_user_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reassign the team manager before removing this user")
    user.team_id = None
    db.add(user)
    log_event(db, actor, "team.member_removed", "Team", team.id, {"user_id": user.id})
    db.commit()
    db.refresh(team)
    return team
