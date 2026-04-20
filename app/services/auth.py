from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models import Team, User
from app.schemas import InviteRequest, SetPasswordRequest
from app.services.audit import log_event


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email, User.active.is_(True)).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return user


def invite_user(db: Session, actor: User, payload: InviteRequest) -> dict:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    team = db.get(Team, payload.team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    invite_token = secrets.token_urlsafe(24)
    user = User(
        email=payload.email,
        name=payload.name,
        role=payload.role,
        team_id=payload.team_id,
        active=True,
        invite_token=invite_token,
        invite_expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(user)
    db.flush()
    log_event(db, actor, "user.invited", "User", user.id, {"email": user.email, "role": user.role, "team_id": user.team_id})
    db.commit()
    db.refresh(user)
    return {"user": user, "invite_token": invite_token}


def set_password_from_invite(db: Session, payload: SetPasswordRequest) -> User:
    user = db.query(User).filter(User.invite_token == payload.token, User.active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite token not found")
    if user.invite_expires_at and user.invite_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite token expired")

    user.hashed_password = get_password_hash(payload.password)
    user.invite_token = None
    user.invite_expires_at = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
