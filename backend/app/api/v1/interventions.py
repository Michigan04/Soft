from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user, require_staff
from app.db.session import get_db
from app.models.enums import InterventionStatus, UserRole
from app.models.intervention import Intervention
from app.models.student import Student
from app.models.user import User
from app.schemas.intervention import InterventionCreate, InterventionOut, InterventionUpdate
from app.services.audit_service import record_audit_event
from app.services.intervention_service import create_intervention, is_overdue, update_intervention

router = APIRouter(prefix="/interventions", tags=["interventions"])


def _serialize(i: Intervention) -> InterventionOut:
    return InterventionOut(
        id=i.id, student_id=i.student_id, staff_user_id=i.staff_user_id,
        staff_user_name=i.staff_user.full_name if i.staff_user else None,
        intervention_type=i.intervention_type, description=i.description, status=i.status,
        outcome=i.outcome, follow_up_date=i.follow_up_date, completed_at=i.completed_at,
        created_at=i.created_at, updated_at=i.updated_at,
        history=[
            {"changed_at": h.changed_at, "field_changed": h.field_changed, "old_value": h.old_value, "new_value": h.new_value}
            for h in i.history
        ],
    )


@router.get("", response_model=list[InterventionOut])
def list_interventions(
    student_id: str | None = None,
    staff_user_id: str | None = None,
    overdue_only: bool = False,
    status_filter: InterventionStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[InterventionOut]:
    query = select(Intervention)
    if student_id:
        query = query.where(Intervention.student_id == student_id)
    if staff_user_id:
        query = query.where(Intervention.staff_user_id == staff_user_id)
    if status_filter:
        query = query.where(Intervention.status == status_filter)

    if current_user.role == UserRole.student:
        student = db.execute(select(Student).where(Student.user_id == current_user.id)).scalar_one_or_none()
        if student is None:
            return []
        query = query.where(Intervention.student_id == student.id)
    elif current_user.role in (UserRole.faculty, UserRole.ta) and not staff_user_id:
        query = query.where(Intervention.staff_user_id == current_user.id)

    interventions = db.execute(query.order_by(Intervention.created_at.desc())).scalars().all()
    if overdue_only:
        interventions = [i for i in interventions if is_overdue(i)]
    return [_serialize(i) for i in interventions]


@router.post("", response_model=InterventionOut, status_code=status.HTTP_201_CREATED)
def create(
    payload: InterventionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_staff)
) -> InterventionOut:
    intervention = create_intervention(db, payload, current_user.id)
    record_audit_event(
        db, actor_user_id=current_user.id, action="create", entity_type="intervention", entity_id=intervention.id,
        after_data={"student_id": intervention.student_id, "intervention_type": intervention.intervention_type.value},
    )
    return _serialize(intervention)


@router.patch("/{intervention_id}", response_model=InterventionOut)
def update(
    intervention_id: str, payload: InterventionUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_staff)
) -> InterventionOut:
    intervention = db.get(Intervention, intervention_id)
    if intervention is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention not found")
    if current_user.role != UserRole.admin and intervention.staff_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own interventions")

    before = {"status": intervention.status.value, "outcome": intervention.outcome.value if intervention.outcome else None}
    intervention = update_intervention(db, intervention, payload, current_user.id)
    record_audit_event(
        db, actor_user_id=current_user.id, action="update", entity_type="intervention", entity_id=intervention.id,
        before_data=before, after_data=payload.model_dump(exclude_unset=True, mode="json"),
    )
    return _serialize(intervention)
