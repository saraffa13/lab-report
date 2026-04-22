"""Thin helper for writing audit log entries from anywhere in the codebase."""
from __future__ import annotations

import logging
from typing import Any

from apps.core.context import get_current_lab_id, get_current_request_id, get_current_user_id

logger = logging.getLogger("labreport.audit")


def log_action(
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    changes: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    user=None,
    lab=None,
) -> None:
    """Write an audit row. Gracefully no-ops if the table isn't migrated yet."""
    try:
        from .models import AuditLog

        lab_id = getattr(lab, "id", None) or get_current_lab_id()
        user_id = getattr(user, "id", None) or get_current_user_id()
        meta = dict(metadata or {})
        if rid := get_current_request_id():
            meta.setdefault("request_id", rid)
        AuditLog.objects.create(
            lab_id=lab_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            changes=changes or {},
            metadata=meta,
        )
    except Exception:
        logger.exception("audit.write.failed", extra={"action": action, "entity": entity_type})
