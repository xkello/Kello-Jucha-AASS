from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1
    actor_id: int | None = None
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class TimesheetSubmitted(BaseEvent):
    event_type: Literal["timesheet.submitted"] = "timesheet.submitted"
    timesheet_id: int
    user_id: int
    total_hours: float
    year: int
    month: int


class ApprovalDecisionMade(BaseEvent):
    event_type: Literal["approval.decision"] = "approval.decision"
    entity_type: str       # "Timesheet" or "AbsenceRequest"
    entity_id: int
    decision: str          # "approved" or "rejected"
    target_user_id: int
    comment: str | None = None


class AbsenceRequested(BaseEvent):
    event_type: Literal["absence.requested"] = "absence.requested"
    absence_id: int
    user_id: int
    absence_type: str
    date_from: str
    date_to: str


class AdminUnlockRequest(BaseEvent):
    event_type: Literal["admin.unlock"] = "admin.unlock"
    entity_type: str
    entity_id: int
    reason: str


# Union type used for type hints across publisher and workers
DomainEvent = TimesheetSubmitted | ApprovalDecisionMade | AbsenceRequested | AdminUnlockRequest
