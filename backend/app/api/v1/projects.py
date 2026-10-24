from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user, require_staff
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.project import Project
from app.models.student import Student
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services.audit_service import record_audit_event

router = APIRouter(prefix="/projects", tags=["projects"])


def _serialize(p: Project) -> ProjectOut:
    return ProjectOut(
        id=p.id, student_id=p.student_id, title=p.title, description=p.description, status=p.status,
        start_date=p.start_date, due_date=p.due_date, completion_date=p.completion_date, grade=p.grade,
        supervisor_id=p.supervisor_id, supervisor_name=p.supervisor.full_name if p.supervisor else None,
    )


@router.get("", response_model=list[ProjectOut])
def list_projects(
    student_id: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[ProjectOut]:
    query = select(Project)
    if student_id:
        query = query.where(Project.student_id == student_id)
    elif current_user.role == UserRole.student:
        student = db.execute(select(Student).where(Student.user_id == current_user.id)).scalar_one_or_none()
        if student is None:
            return []
        query = query.where(Project.student_id == student.id)
    elif current_user.role in (UserRole.faculty, UserRole.ta):
        query = query.join(Student).where(Student.assigned_staff_id == current_user.id)

    projects = db.execute(query).scalars().all()
    return [_serialize(p) for p in projects]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(require_staff)
) -> ProjectOut:
    project = Project(
        student_id=payload.student_id, title=payload.title, description=payload.description,
        start_date=payload.start_date, due_date=payload.due_date, supervisor_id=payload.supervisor_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    record_audit_event(
        db, actor_user_id=current_user.id, action="create", entity_type="project", entity_id=project.id,
        after_data={"title": project.title, "student_id": project.student_id},
    )
    return _serialize(project)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_staff)
) -> ProjectOut:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    before = {"status": project.status.value, "grade": project.grade}
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)

    record_audit_event(
        db, actor_user_id=current_user.id, action="update", entity_type="project", entity_id=project.id,
        before_data=before, after_data=changes,
    )
    return _serialize(project)


router_milestones = APIRouter(prefix="/milestones", tags=["milestones"])


@router_milestones.get("")
def list_milestones(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[dict]:
    from app.models.milestone import AcademicMilestone

    milestones = db.execute(select(AcademicMilestone).order_by(AcademicMilestone.academic_level, AcademicMilestone.sequence_order)).scalars().all()
    return [
        {
            "id": m.id, "name": m.name, "academic_level": m.academic_level.value, "description": m.description,
            "required_credits": m.required_credits, "target_cgpa": float(m.target_cgpa) if m.target_cgpa else None,
            "sequence_order": m.sequence_order, "is_active": m.is_active,
        }
        for m in milestones
    ]
