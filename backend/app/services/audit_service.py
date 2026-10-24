from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def record_audit_event(
    db: Session,
    *,
    actor_user_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    before_data: dict | None = None,
    after_data: dict | None = None,
    ip_address: str | None = None,
    commit: bool = True,
) -> AuditLog:
    """Persist an immutable audit record. There is no API to edit or delete audit logs (US-11)."""
    entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_data=before_data,
        after_data=after_data,
        ip_address=ip_address,
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    return entry
