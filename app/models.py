from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum as SAEnum, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RoleEnum(str, Enum):
    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"


class TimesheetStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AbsenceType(str, Enum):
    VACATION = "VACATION"
    SICK = "SICK"


class AbsenceStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class DayType(str, Enum):
    WORK = "WORK"
    VACATION = "VACATION"
    SICK = "SICK"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Team(TimestampMixin, Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    manager_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    manager: Mapped["User"] = relationship(foreign_keys=[manager_user_id], post_update=True)
    members: Mapped[list["User"]] = relationship(back_populates="team", foreign_keys="User.team_id")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(SAEnum(RoleEnum, native_enum=False), nullable=False, default=RoleEnum.EMPLOYEE)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)
    invite_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    invite_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    team: Mapped["Team"] = relationship(back_populates="members", foreign_keys=[team_id])


class Timesheet(TimestampMixin, Base):
    __tablename__ = "timesheets"
    __table_args__ = (UniqueConstraint("user_id", "month", "year", name="uq_user_month_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    month: Mapped[int] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[TimesheetStatus] = mapped_column(
        SAEnum(TimesheetStatus, native_enum=False), default=TimesheetStatus.DRAFT, nullable=False
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    approver_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    rejection_comment: Mapped[str] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    approver: Mapped["User"] = relationship(foreign_keys=[approver_user_id])
    days: Mapped[list["TimesheetDay"]] = relationship(back_populates="timesheet", cascade="all, delete-orphan")


class TimesheetDay(TimestampMixin, Base):
    __tablename__ = "timesheet_days"
    __table_args__ = (UniqueConstraint("timesheet_id", "date", name="uq_timesheet_day_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    timesheet_id: Mapped[int] = mapped_column(ForeignKey("timesheets.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    day_type: Mapped[DayType] = mapped_column(SAEnum(DayType, native_enum=False), nullable=False, default=DayType.WORK)

    timesheet: Mapped["Timesheet"] = relationship(back_populates="days")


class AbsenceRequest(TimestampMixin, Base):
    __tablename__ = "absence_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[AbsenceType] = mapped_column(SAEnum(AbsenceType, native_enum=False), nullable=False)
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AbsenceStatus] = mapped_column(
        SAEnum(AbsenceStatus, native_enum=False), default=AbsenceStatus.REQUESTED, nullable=False
    )
    approver_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    approver: Mapped["User"] = relationship(foreign_keys=[approver_user_id])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    details_json: Mapped[dict] = mapped_column(JSON, nullable=True)

    actor: Mapped["User"] = relationship(foreign_keys=[actor_user_id])
