from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user
from app.db.session import get_db
from app.models.enums import AcademicLevel, InterventionStatus, RiskLevel, UserRole
from app.models.intervention import Intervention
from app.models.notification import Notification
from app.models.student import Student
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, ProgressionTrendPoint, RiskDistributionItem
from app.services.cgpa_service import compute_cgpa
from app.services.intervention_service import is_overdue
from app.services.risk_engine import get_latest_assessment

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _scoped_students(db: Session, current_user: User, academic_level: AcademicLevel | None) -> list[Student]:
    query = select(Student)
    if academic_level:
        query = query.where(Student.academic_level == academic_level)
    if current_user.role in (UserRole.faculty, UserRole.ta):
        query = query.where(Student.assigned_staff_id == current_user.id)
    return list(db.execute(query).scalars().all())


@router.get("/summary", response_model=DashboardSummary)
def summary(
    academic_level: AcademicLevel | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> DashboardSummary:
    students = _scoped_students(db, current_user, academic_level)
    student_ids = {s.id for s in students}

    at_risk = high_risk = critical_risk = 0
    for s in students:
        latest = get_latest_assessment(db, s.id)
        if latest and latest.risk_level != RiskLevel.low:
            at_risk += 1
        if latest and latest.risk_level == RiskLevel.high:
            high_risk += 1
        if latest and latest.risk_level == RiskLevel.critical:
            critical_risk += 1

    interventions = db.execute(select(Intervention)).scalars().all()
    if current_user.role in (UserRole.faculty, UserRole.ta):
        interventions = [i for i in interventions if i.student_id in student_ids]
    pending_interventions = sum(1 for i in interventions if i.status in (InterventionStatus.open, InterventionStatus.in_progress))
    overdue_followups = sum(1 for i in interventions if is_overdue(i))

    unread = db.execute(select(Notification).where(Notification.user_id == current_user.id, Notification.is_read.is_(False))).scalars().all()

    return DashboardSummary(
        total_students=len(students), at_risk_students=at_risk, high_risk_students=high_risk,
        critical_risk_students=critical_risk, pending_interventions=pending_interventions,
        overdue_followups=overdue_followups, unread_notifications=len(unread),
    )


@router.get("/risk-distribution", response_model=list[RiskDistributionItem])
def risk_distribution(
    academic_level: AcademicLevel | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[RiskDistributionItem]:
    students = _scoped_students(db, current_user, academic_level)
    counts = {level.value: 0 for level in RiskLevel}
    counts["unassessed"] = 0
    for s in students:
        latest = get_latest_assessment(db, s.id)
        if latest:
            counts[latest.risk_level.value] += 1
        else:
            counts["unassessed"] += 1
    return [RiskDistributionItem(risk_level=level, count=count) for level, count in counts.items()]


@router.get("/progression-trends", response_model=list[ProgressionTrendPoint])
def progression_trends(
    academic_level: AcademicLevel | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[ProgressionTrendPoint]:
    """Aggregates current CGPA and at-risk counts by academic level as a simple
    'progression' snapshot (one point per level, since fine-grained historical
    CGPA-by-term is not tracked separately from course_results)."""
    students = _scoped_students(db, current_user, academic_level)
    by_level: dict[str, list[Student]] = {}
    for s in students:
        by_level.setdefault(s.academic_level.value, []).append(s)

    points = []
    for level, level_students in by_level.items():
        cgpas = []
        at_risk_count = 0
        for s in level_students:
            cgpa, _completed, _attempted = compute_cgpa(db, s.id)
            if cgpa is not None:
                cgpas.append(cgpa)
            latest = get_latest_assessment(db, s.id)
            if latest and latest.risk_level != RiskLevel.low:
                at_risk_count += 1
        points.append(
            ProgressionTrendPoint(
                period=level, average_cgpa=round(sum(cgpas) / len(cgpas), 2) if cgpas else None,
                at_risk_count=at_risk_count, total_students=len(level_students),
            )
        )
    return points
