from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.admin import AdminAction


def log_admin_action(
    db: Session,
    *,
    admin_user_id: int | None,
    action_type: str,
    target_type: str | None = None,
    target_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    db.add(
        AdminAction(
            admin_user_id=admin_user_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            metadata_json=metadata or {},
        )
    )
    db.commit()
