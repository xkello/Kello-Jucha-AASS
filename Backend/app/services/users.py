from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models import RoleEnum, Team, User
from app.schemas import UserCreate, UserUpdate
from app.services.audit import log_event


def create_user(db: Session, actor: User, payload: UserCreate) -> User:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    if payload.team_id is not None and not db.get(Team, payload.team_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    user = User(
        email=payload.email,
        name=payload.name,
        role=payload.role,
        team_id=payload.team_id,
        active=True,
        hashed_password=get_password_hash(payload.password or settings.demo_password),
    )
    db.add(user)
    db.flush()
    log_event(db, actor, "user.created", "User", user.id, {"role": user.role, "team_id": user.team_id})
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, actor: User, user: User, payload: UserUpdate) -> User:
    before = {"name": user.name, "role": user.role, "team_id": user.team_id, "active": user.active}

    if payload.team_id is not None and not db.get(Team, payload.team_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    if user.role == RoleEnum.EMPLOYEE:
        managed_team = db.query(Team).filter(Team.manager_user_id == user.id).first()
        if managed_team:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A team manager cannot be downgraded while managing a team")

    db.add(user)
    log_event(db, actor, "user.updated", "User", user.id, {"before": before, "after": payload.model_dump(exclude_unset=True)})
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, actor: User, user: User) -> User:
    user.active = False
    db.add(user)
    log_event(db, actor, "user.deactivated", "User", user.id, {"email": user.email})
    db.commit()
    db.refresh(user)
    return user
