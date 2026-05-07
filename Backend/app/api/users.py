from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import RoleEnum, User
from app.schemas import UserCreate, UserRead, UserUpdate
from app.services.users import create_user, deactivate_user, update_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(User)
    if current_user.role == RoleEnum.ADMIN:
        return query.order_by(User.id).all()
    if current_user.role == RoleEnum.MANAGER and current_user.team_id is not None:
        return query.filter(User.team_id == current_user.team_id).order_by(User.id).all()
    return [current_user]


@router.post("", response_model=UserRead)
def create_user_endpoint(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    return create_user(db, current_user, payload)


@router.patch("/{user_id}", response_model=UserRead)
def update_user_endpoint(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return update_user(db, current_user, user, payload)


@router.delete("/{user_id}", response_model=UserRead)
def deactivate_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return deactivate_user(db, current_user, user)
