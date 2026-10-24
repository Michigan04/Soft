import math
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import get_accessible_student, get_current_user, require_staff
from app.db.session import get_db
from app.models.enums import AcademicLevel, MilestoneStatus, ProgramStatus, RiskLevel, UserRole
from app.models.intervention import Intervention
from app.models.milestone import AcademicMilestone, StudentMilestone
from app.models.notification import Notification
from app.models.project import Project
from app.models.registration import Registration
from app.models.result import CourseResult
from app.models.student import Student
from app.models.user import User
from app.schemas.academic import CourseResultOut
from app.schemas.common import PaginatedResponse
from app.schemas.intervention import InterventionOut
from app.schemas.notification import NotificationOut
from app.schemas.project import ProjectOut
from app.schemas.registration import RegistrationOut
from app.schemas.risk import RiskAssessmentOut
from app.schemas.student import StudentCreate, StudentDetail, StudentListItem, StudentUpdate
from app.core.security import hash_password
from app.services.audit_service import record_audit_event
from app.services.cgpa_service import compute_cgpa, project_target_cgpa_scenarios
from app.services.intervention_service import is_overdue
from app.services.risk_engine import assess_student_risk, get_latest_assessment

router = APIRouter(prefix="/students", tags=["students"])

RISK_LEVEL_ORDER = {level: idx for idx, level in enumerate([RiskLevel.low, RiskLevel.moderate, RiskLevel.high, RiskLevel.critical])}


def _to_list_item(db: Session, student: Student) -> StudentListItem:
    cgpa, _completed, _attempted = compute_cgpa(db, student.id)
    latest = get_latest_assessment(db, student.id)
    pending_followups = db.query(Intervention).filter(
        Intervention.student_id == student.id, Intervention.follow_up_date.isnot(None)
    ).all()
    overdue_count = sum(1 for i in pending_followups if is_overdue(i))

    primary_reason = None
    if latest and latest.factors:
        sorted_factors = sorted(latest.factors, key=lambda f: f.points_contributed, reverse=True)
        primary_reason = sorted_factors[0].factor_name if sorted_factors else None

    return StudentListItem(
        id=student.id,
        student_identifier=student.student_identifier,
        full_name=student.full_name,
        academic_level=student.academic_level,
        program_status=student.program_status,
        current_term=student.current_term,
        assigned_staff_id=student.assigned_staff_id,
        assigned_staff_name=student.assigned_staff.full_name if student.assigned_staff else None,
        cgpa=cgpa,
        latest_risk_level=latest.risk_level if latest else None,
        latest_risk_score=float(latest.risk_score) if latest else None,
        primary_risk_reason=primary_reason,
        latest_assessment_date=latest.assessment_date if latest else None,
        pending_followups=overdue_count,
    )


@router.get("", response_model=PaginatedResponse[StudentListItem])
def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    academic_level: AcademicLevel | None = None,
    risk_level: RiskLevel | None = None,
    program_status: ProgramStatus | None = None,
    assigned_staff_id: str | None = None,
    risk_increased_only: bool = False,
    sort_by: str = Query("risk_score", pattern="^(risk_score|latest_assessment|pending_followups|full_name)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[StudentListItem]:
    query = select(Student)
    if academic_level:
        query = query.where(Student.academic_level == academic_level)
    if program_status:
        query = query.where(Student.program_status == program_status)
    if assigned_staff_id:
        query = query.where(Student.assigned_staff_id == assigned_staff_id)
    if search:
        like = f"%{search.lower()}%"
        query = query.where(
            Student.full_name.ilike(like) | Student.student_identifier.ilike(like)
        )
    if current_user.role in (UserRole.faculty, UserRole.ta):
        query = query.where(Student.assigned_staff_id == current_user.id)
    elif current_user.role == UserRole.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students cannot list other students")

    students = db.execute(query).scalars().all()
    items = [_to_list_item(db, s) for s in students]

    if risk_level:
        items = [i for i in items if i.latest_risk_level == risk_level]

    if risk_increased_only:
        from app.models.risk import RiskAssessment

        escalated_ids = set()
        for s in students:
            history = db.execute(
                select(RiskAssessment).where(RiskAssessment.student_id == s.id).order_by(RiskAssessment.assessment_date.desc()).limit(2)
            ).scalars().all()
            if len(history) == 2 and RISK_LEVEL_ORDER[history[0].risk_level] > RISK_LEVEL_ORDER[history[1].risk_level]:
                escalated_ids.add(s.id)
        items = [i for i in items if i.id in escalated_ids]

    reverse = sort_dir == "desc"
    if sort_by == "risk_score":
        items.sort(key=lambda i: (i.latest_risk_score is not None, i.latest_risk_score or 0), reverse=reverse)
    elif sort_by == "latest_assessment":
        items.sort(key=lambda i: (i.latest_assessment_date is not None, i.latest_assessment_date), reverse=reverse)
    elif sort_by == "pending_followups":
        items.sort(key=lambda i: i.pending_followups, reverse=reverse)
    else:
        items.sort(key=lambda i: i.full_name.lower(), reverse=reverse)

    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]
    pages = math.ceil(total / page_size) if total else 1

    return PaginatedResponse(items=page_items, total=total, page=page, page_size=page_size, pages=pages)


@router.post("", response_model=StudentDetail, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate, db: Session = Depends(get_db), current_user: User = Depends(require_staff)
) -> StudentDetail:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create students")

    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with this email already exists")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.student,
    )
    db.add(user)
    db.flush()

    student = Student(
        student_identifier=payload.student_identifier,
        user_id=user.id,
        full_name=payload.full_name,
        academic_level=payload.academic_level,
        admission_date=payload.admission_date,
        current_term=payload.current_term,
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    record_audit_event(
        db, actor_user_id=current_user.id, action="create", entity_type="student", entity_id=student.id,
        after_data={"student_identifier": student.student_identifier, "full_name": student.full_name},
    )
    return StudentDetail(
        id=student.id, student_identifier=student.student_identifier, full_name=student.full_name,
        academic_level=student.academic_level, program_status=student.program_status,
        admission_date=student.admission_date, current_term=student.current_term,
        assigned_staff_id=student.assigned_staff_id, assigned_staff_name=None,
    )


@router.get("/{student_id}", response_model=StudentDetail)
def get_student(student: Student = Depends(get_accessible_student)) -> StudentDetail:
    return StudentDetail(
        id=student.id, student_identifier=student.student_identifier, full_name=student.full_name,
        academic_level=student.academic_level, program_status=student.program_status,
        admission_date=student.admission_date, current_term=student.current_term,
        assigned_staff_id=student.assigned_staff_id,
        assigned_staff_name=student.assigned_staff.full_name if student.assigned_staff else None,
    )


@router.patch("/{student_id}", response_model=StudentDetail)
def update_student(
    payload: StudentUpdate,
    student: Student = Depends(get_accessible_student),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentDetail:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update student records")

    before = {"full_name": student.full_name, "academic_level": student.academic_level.value, "program_status": student.program_status.value}
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)

    record_audit_event(
        db, actor_user_id=current_user.id, action="update", entity_type="student", entity_id=student.id,
        before_data=before, after_data=changes,
    )
    return StudentDetail(
        id=student.id, student_identifier=student.student_identifier, full_name=student.full_name,
        academic_level=student.academic_level, program_status=student.program_status,
        admission_date=student.admission_date, current_term=student.current_term,
        assigned_staff_id=student.assigned_staff_id,
        assigned_staff_name=student.assigned_staff.full_name if student.assigned_staff else None,
    )


@router.get("/{student_id}/academic-history")
def academic_history(student: Student = Depends(get_accessible_student), db: Session = Depends(get_db)) -> dict:
    results = db.execute(select(CourseResult).where(CourseResult.student_id == student.id)).scalars().all()
    registrations = db.execute(select(Registration).where(Registration.student_id == student.id)).scalars().all()
    milestones = db.execute(select(StudentMilestone).where(StudentMilestone.student_id == student.id)).scalars().all()
    cgpa, completed_credits, attempted_credits = compute_cgpa(db, student.id)

    return {
        "cgpa": cgpa,
        "completed_credits": completed_credits,
        "total_attempted_credits": attempted_credits,
        "course_results": [
            CourseResultOut(
                id=r.id, course_id=r.course_id, course_code=r.course.course_code, course_name=r.course.course_name,
                academic_term_id=r.academic_term_id, academic_term_name=r.academic_term.name, grade=r.grade,
                grade_points=float(r.grade_points) if r.grade_points is not None else None, credits=r.credits,
                result_status=r.result_status, recorded_at=r.recorded_at,
            ).model_dump(mode="json")
            for r in results
        ],
        "registrations": [
            RegistrationOut(
                id=r.id, student_id=r.student_id, course_id=r.course_id, course_code=r.course.course_code,
                course_name=r.course.course_name, academic_term_id=r.academic_term_id, status=r.status,
                validation_status=r.validation_status, validation_errors=r.validation_errors,
            ).model_dump(mode="json")
            for r in registrations
        ],
        "milestones": [
            {
                "id": m.id, "milestone_name": m.milestone.name, "status": m.status.value,
                "completed_at": m.completed_at.isoformat() if m.completed_at else None, "notes": m.notes,
            }
            for m in milestones
        ],
    }


@router.get("/{student_id}/risk-assessments", response_model=list[RiskAssessmentOut])
def risk_assessments(student: Student = Depends(get_accessible_student), db: Session = Depends(get_db)) -> list:
    from app.models.risk import RiskAssessment

    assessments = db.execute(
        select(RiskAssessment).where(RiskAssessment.student_id == student.id).order_by(RiskAssessment.assessment_date.desc())
    ).scalars().all()
    return assessments


@router.post("/{student_id}/assess-risk", response_model=RiskAssessmentOut)
def trigger_risk_assessment(
    student: Student = Depends(get_accessible_student),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> RiskAssessmentOut:
    assessment = assess_student_risk(db, student)
    record_audit_event(
        db, actor_user_id=current_user.id, action="assess_risk", entity_type="student", entity_id=student.id,
        after_data={"risk_score": float(assessment.risk_score), "risk_level": assessment.risk_level.value},
    )
    return assessment


@router.get("/{student_id}/interventions", response_model=list[InterventionOut])
def student_interventions(student: Student = Depends(get_accessible_student), db: Session = Depends(get_db)) -> list:
    interventions = db.execute(
        select(Intervention).where(Intervention.student_id == student.id).order_by(Intervention.created_at.desc())
    ).scalars().all()
    results = []
    for i in interventions:
        results.append(
            InterventionOut(
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
        )
    return results


@router.get("/{student_id}/milestones")
def student_milestones(student: Student = Depends(get_accessible_student), db: Session = Depends(get_db)) -> list[dict]:
    all_milestones = db.execute(
        select(AcademicMilestone).where(AcademicMilestone.academic_level == student.academic_level, AcademicMilestone.is_active.is_(True))
        .order_by(AcademicMilestone.sequence_order)
    ).scalars().all()
    student_progress = {
        m.milestone_id: m
        for m in db.execute(select(StudentMilestone).where(StudentMilestone.student_id == student.id)).scalars().all()
    }
    return [
        {
            "milestone_id": m.id,
            "name": m.name,
            "description": m.description,
            "required_credits": m.required_credits,
            "target_cgpa": float(m.target_cgpa) if m.target_cgpa is not None else None,
            "sequence_order": m.sequence_order,
            "status": student_progress[m.id].status.value if m.id in student_progress else MilestoneStatus.not_started.value,
            "completed_at": student_progress[m.id].completed_at.isoformat() if m.id in student_progress and student_progress[m.id].completed_at else None,
        }
        for m in all_milestones
    ]


@router.get("/{student_id}/projects", response_model=list[ProjectOut])
def student_projects(student: Student = Depends(get_accessible_student), db: Session = Depends(get_db)) -> list:
    projects = db.execute(select(Project).where(Project.student_id == student.id)).scalars().all()
    return [
        ProjectOut(
            id=p.id, student_id=p.student_id, title=p.title, description=p.description, status=p.status,
            start_date=p.start_date, due_date=p.due_date, completion_date=p.completion_date, grade=p.grade,
            supervisor_id=p.supervisor_id, supervisor_name=p.supervisor.full_name if p.supervisor else None,
        )
        for p in projects
    ]


@router.get("/{student_id}/cgpa-summary")
def cgpa_summary(student: Student = Depends(get_accessible_student), db: Session = Depends(get_db)) -> dict:
    cgpa, completed_credits, attempted_credits = compute_cgpa(db, student.id)
    milestones = db.execute(
        select(AcademicMilestone).where(AcademicMilestone.academic_level == student.academic_level, AcademicMilestone.is_active.is_(True))
    ).scalars().all()
    student_progress = {
        m.milestone_id
        for m in db.execute(select(StudentMilestone).where(StudentMilestone.student_id == student.id, StudentMilestone.status == MilestoneStatus.completed)).scalars().all()
    }
    pending_requirements = [m.name for m in milestones if m.id not in student_progress]

    remaining_credits = max(0, (milestones[-1].required_credits or 0) - completed_credits) if milestones else 0
    scenarios = project_target_cgpa_scenarios(db, student.id, remaining_credits)

    from app.services.policy_service import get_policy
    assumptions_policy = get_policy(db, "cgpa_assumptions")

    return {
        "current_cgpa": cgpa,
        "completed_credits": completed_credits,
        "total_attempted_credits": attempted_credits,
        "pending_requirements": pending_requirements,
        "target_scenarios": scenarios,
        "assumptions": [
            f"Grade point scale assumed 0-{assumptions_policy.get('max_grade_points', 10)}.",
            "CGPA is credit-weighted across all graded (pass/fail) results; incomplete/withdrawn results are excluded.",
            "Target-CGPA projections assume remaining credits are graded at a uniform average; actual course-by-course performance will vary.",
        ],
    }


@router.get("/{student_id}/notifications", response_model=list[NotificationOut])
def student_notifications(student: Student = Depends(get_accessible_student), db: Session = Depends(get_db)) -> list:
    notifications = db.execute(
        select(Notification).where(Notification.student_id == student.id).order_by(Notification.created_at.desc())
    ).scalars().all()
    return notifications
