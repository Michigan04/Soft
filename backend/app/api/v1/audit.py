import math
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_admin
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogOut
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=PaginatedResponse[AuditLogOut])
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    actor_user_id: str | None = None,
    entity_type: str | None = None,
    action: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> PaginatedResponse[AuditLogOut]:
    query = select(AuditLog)
    if actor_user_id:
        query = query.where(AuditLog.actor_user_id == actor_user_id)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if action:
        query = query.where(AuditLog.action == action)
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)

    all_logs = db.execute(query.order_by(AuditLog.created_at.desc())).scalars().all()
    total = len(all_logs)
    start = (page - 1) * page_size
    page_logs = all_logs[start : start + page_size]

    items = [
        AuditLogOut(
            id=log.id, actor_user_id=log.actor_user_id, actor_name=log.actor.full_name if log.actor else None,
            action=log.action, entity_type=log.entity_type, entity_id=log.entity_id,
            before_data=log.before_data, after_data=log.after_data, created_at=log.created_at,
        )
        for log in page_logs
    ]
    pages = math.ceil(total / page_size) if total else 1
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)
