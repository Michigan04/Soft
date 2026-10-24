import csv
import io
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import AcademicLevel, InterventionStatus, RiskLevel
from app.models.intervention import Intervention
from app.models.risk import RiskAssessment
from app.models.student import Student
from app.services.cgpa_service import compute_cgpa


def risk_trends(
    db: Session, start_date: date | None, end_date: date | None, academic_level: AcademicLevel | None
) -> list[dict]:
    query = select(RiskAssessment, Student).join(Student, RiskAssessment.student_id == Student.id)
    if start_date:
        query = query.where(RiskAssessment.assessment_date >= start_date)
    if end_date:
        query = query.where(RiskAssessment.assessment_date <= end_date)
    if academic_level:
        query = query.where(Student.academic_level == academic_level)

    rows = db.execute(query).all()
    buckets: dict[str, dict[str, int]] = {}
    for assessment, _student in rows:
        period = assessment.assessment_date.strftime("%Y-%m")
        buckets.setdefault(period, {level.value: 0 for level in RiskLevel})
        buckets[period][assessment.risk_level.value] += 1

    return [{"period": period, **counts} for period, counts in sorted(buckets.items())]


def intervention_outcomes(
    db: Session, start_date: date | None, end_date: date | None, staff_user_id: str | None
) -> list[dict]:
    query = select(Intervention)
    if start_date:
        query = query.where(Intervention.created_at >= start_date)
    if end_date:
        query = query.where(Intervention.created_at <= end_date)
    if staff_user_id:
        query = query.where(Intervention.staff_user_id == staff_user_id)

    interventions = db.execute(query).scalars().all()
    outcome_counts: dict[str, int] = {}
    for i in interventions:
        key = i.outcome.value if i.outcome else "pending"
        outcome_counts[key] = outcome_counts.get(key, 0) + 1

    return [{"outcome": k, "count": v} for k, v in sorted(outcome_counts.items())]


def progression_report(db: Session, academic_level: AcademicLevel | None) -> list[dict]:
    query = select(Student)
    if academic_level:
        query = query.where(Student.academic_level == academic_level)
    students = db.execute(query).scalars().all()

    by_level: dict[str, list[float]] = {}
    for s in students:
        cgpa, _completed, _attempted = compute_cgpa(db, s.id)
        if cgpa is not None:
            by_level.setdefault(s.academic_level.value, []).append(cgpa)
        else:
            by_level.setdefault(s.academic_level.value, [])

    return [
        {
            "academic_level": level,
            "student_count": len([s for s in students if s.academic_level.value == level]),
            "average_cgpa": round(sum(values) / len(values), 2) if values else None,
        }
        for level, values in by_level.items()
    ]


def overdue_followups_report(db: Session) -> list[dict]:
    today = date.today()
    interventions = db.execute(
        select(Intervention).where(
            Intervention.follow_up_date < today,
            Intervention.status.notin_([InterventionStatus.completed, InterventionStatus.cancelled]),
        )
    ).scalars().all()
    return [
        {
            "intervention_id": i.id,
            "student_id": i.student_id,
            "staff_user_id": i.staff_user_id,
            "follow_up_date": i.follow_up_date.isoformat() if i.follow_up_date else None,
            "status": i.status.value,
            "days_overdue": (today - i.follow_up_date).days if i.follow_up_date else None,
        }
        for i in interventions
    ]


def rows_to_csv(rows: list[dict]) -> str:
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
