from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.security import create_access_token
from app.models import RoleEnum, User
from app.schemas import InviteRequest, LoginRequest, SetPasswordRequest, TokenResponse, UserRead
from app.services.auth import authenticate_user, invite_user, set_password_from_invite

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    return TokenResponse(access_token=create_access_token(user.email))


@router.post("/invite")
def invite(
    payload: InviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    result = invite_user(db, current_user, payload)
    return {
        "message": "User invited",
        "invite_token": result["invite_token"],
        "user": UserRead.model_validate(result["user"]),
    }


@router.post("/set-password", response_model=UserRead)
def set_password(payload: SetPasswordRequest, db: Session = Depends(get_db)):
    return set_password_from_invite(db, payload)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user
