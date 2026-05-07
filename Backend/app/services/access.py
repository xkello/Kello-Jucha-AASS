from fastapi import HTTPException, status

from app.models import RoleEnum, User


def is_manager_of(actor: User, target: User) -> bool:
    return actor.role == RoleEnum.MANAGER and actor.team_id is not None and actor.team_id == target.team_id and actor.id != target.id


def ensure_same_user_or_privileged(actor: User, target: User) -> None:
    if actor.role == RoleEnum.ADMIN or actor.id == target.id or is_manager_of(actor, target):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized for this resource")


def ensure_manager_or_admin_for_target(actor: User, target: User) -> None:
    if actor.role == RoleEnum.ADMIN or is_manager_of(actor, target):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the correct manager or admin can perform this action")
