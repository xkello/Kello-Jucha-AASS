from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy.orm import Session

from app.models import AuditLog, User


def _to_json_safe(value):
    if isinstance(value, dict):
        return {k: _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_json_safe(v) for v in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


def log_event(db: Session, actor: User | None, action: str, entity_type: str, entity_id: str | int, details: dict | None = None) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor.id if actor else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            details_json=_to_json_safe(details or {}),
        )
    )
