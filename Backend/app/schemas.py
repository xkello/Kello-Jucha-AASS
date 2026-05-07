from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import AbsenceStatus, AbsenceType, DayType, RoleEnum, TimesheetStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    manager_user_id: int | None = None


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    manager_user_id: int | None = None
    active: bool | None = None


class UserCreate(BaseModel):
    email: str
    name: str
    role: RoleEnum = RoleEnum.EMPLOYEE
    team_id: int | None = None
    password: str | None = None


class InviteRequest(BaseModel):
    email: str
    name: str
    role: RoleEnum = RoleEnum.EMPLOYEE
    team_id: int


class SetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=6)


class UserUpdate(BaseModel):
    name: str | None = None
    role: RoleEnum | None = None
    team_id: int | None = None
    active: bool | None = None


class AddMemberRequest(BaseModel):
    user_id: int


class TeamRead(ORMModel):
    id: int
    name: str
    manager_user_id: int | None
    active: bool


class UserRead(ORMModel):
    id: int
    email: str
    name: str
    role: RoleEnum
    team_id: int | None
    active: bool


class DayEntryCreate(BaseModel):
    date: date
    hours: float = Field(ge=0, le=24)
    day_type: DayType = DayType.WORK


class DayEntryUpdate(BaseModel):
    hours: float = Field(ge=0, le=24)


class TimesheetActionRequest(BaseModel):
    comment: str | None = None


class UnlockRequest(BaseModel):
    reason: str = Field(min_length=3)


class TimesheetDayRead(ORMModel):
    id: int
    date: date
    hours: float
    day_type: DayType


class TimesheetRead(ORMModel):
    id: int
    user_id: int
    user_name: str | None = None
    month: int
    year: int
    status: TimesheetStatus
    rejection_comment: str | None
    submitted_at: datetime | None
    approved_at: datetime | None
    approver_user_id: int | None
    days: list[TimesheetDayRead]


class AbsenceCreate(BaseModel):
    type: AbsenceType
    date_from: date
    date_to: date
    comment: str | None = None


class AbsenceRead(ORMModel):
    id: int
    user_id: int
    type: AbsenceType
    date_from: date
    date_to: date
    status: AbsenceStatus
    approver_user_id: int | None
    comment: str | None


class AuditLogRead(ORMModel):
    id: int
    actor_user_id: int | None
    action: str
    entity_type: str
    entity_id: str
    timestamp: datetime
    details_json: dict | None
