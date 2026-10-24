from datetime import date

from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.models.enums import InterventionStatus
from app.models.intervention import Intervention, InterventionHistory
from app.schemas.intervention import InterventionCreate, InterventionUpdate


def create_intervention(db: Session, data: InterventionCreate, staff_user_id: str) -> Intervention:
    intervention = Intervention(
        student_id=data.student_id,
        staff_user_id=staff_user_id,
        intervention_type=data.intervention_type,
        description=data.description,
        follow_up_date=data.follow_up_date,
    )
    db.add(intervention)
    db.flush()
    db.add(
        InterventionHistory(
            intervention_id=intervention.id,
            changed_by=staff_user_id,
            field_changed="created",
            old_value=None,
            new_value=data.intervention_type.value,
        )
    )
    db.commit()
    db.refresh(intervention)
    return intervention


def update_intervention(db: Session, intervention: Intervention, data: InterventionUpdate, changed_by: str) -> Intervention:
    changes = data.model_dump(exclude_unset=True)
    for field, new_value in changes.items():
        old_value = getattr(intervention, field)
        if old_value == new_value:
            continue
        db.add(
            InterventionHistory(
                intervention_id=intervention.id,
                changed_by=changed_by,
                field_changed=field,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else None,
            )
        )
        setattr(intervention, field, new_value)

    if data.status == InterventionStatus.completed and intervention.completed_at is None:
        intervention.completed_at = utcnow()

    db.commit()
    db.refresh(intervention)
    return intervention


def is_overdue(intervention: Intervention) -> bool:
    return bool(
        intervention.follow_up_date
        and intervention.follow_up_date < date.today()
        and intervention.status not in (InterventionStatus.completed, InterventionStatus.cancelled)
    )
