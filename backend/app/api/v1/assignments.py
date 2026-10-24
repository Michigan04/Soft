from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_admin
from app.db.session import get_db
from app.models.assignment import StudentAssignment
from app.models.enums import InterventionStatus, UserRole
from app.models.intervention import Intervention
from app.models.student import Student
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentOut, StaffWorkloadOut
from app.services.audit_service import record_audit_event
from app.services.intervention_service import is_overdue

router = APIRouter(tags=["assignments"])


@router.post("/students/{student_id}/assignments", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def assign_student(
    student_id: str, payload: AssignmentCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> AssignmentOut:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    staff = db.get(User, payload.staff_user_id)
    if staff is None or staff.role not in (UserRole.faculty, UserRole.ta, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="staff_user_id must reference a faculty/TA/admin user")

    previous_staff_id = student.assigned_staff_id

    existing_active = db.execute(
        select(StudentAssignment).where(StudentAssignment.student_id == student_id, StudentAssignment.is_active.is_(True))
    ).scalars().all()
    from app.db.base import utcnow
    for a in existing_active:
        a.is_active = False
        a.unassigned_at = utcnow()

    assignment = StudentAssignment(student_id=student_id, staff_user_id=payload.staff_user_id, assigned_by=current_user.id)
    db.add(assignment)
    student.assigned_staff_id = payload.staff_user_id
    db.commit()
    db.refresh(assignment)

    record_audit_event(
        db, actor_user_id=current_user.id, action="assign", entity_type="student_assignment", entity_id=assignment.id,
        before_data={"assigned_staff_id": previous_staff_id}, after_data={"assigned_staff_id": payload.staff_user_id},
    )
    return assignment


@router.get("/staff/workload", response_model=list[StaffWorkloadOut])
def staff_workload(db: Session = Depends(get_db), current_user: User = Depends(require_admin)) -> list[StaffWorkloadOut]:
    staff_members = db.execute(select(User).where(User.role.in_([UserRole.faculty, UserRole.ta]))).scalars().all()
    today = date.today()
    results = []
    for staff in staff_members:
        assigned_count = db.execute(select(Student).where(Student.assigned_staff_id == staff.id)).scalars().all()
        interventions = db.execute(
            select(Intervention).where(Intervention.staff_user_id == staff.id)
        ).scalars().all()
        open_count = sum(1 for i in interventions if i.status in (InterventionStatus.open, InterventionStatus.in_progress))
        overdue_count = sum(1 for i in interventions if is_overdue(i))
        results.append(
            StaffWorkloadOut(
                staff_user_id=staff.id, staff_name=staff.full_name, role=staff.role.value,
                assigned_student_count=len(assigned_count), open_interventions=open_count, overdue_followups=overdue_count,
            )
        )
    return results
