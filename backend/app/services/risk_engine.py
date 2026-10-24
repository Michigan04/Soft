"""Transparent, rule-based risk identification engine.

This engine is deliberately NOT a trained predictive model. It evaluates a
student's available academic data against a set of admin-configurable
`RiskRule` rows and produces an explainable 0-100 risk score, a risk category,
and a human-readable factor-by-factor breakdown. See docs/RISK_ENGINE.md for
the full scoring formula, assumptions, and limitations.
"""

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import (
    InterventionStatus,
    MilestoneStatus,
    ProjectStatus,
    RegistrationStatus,
    ResultStatus,
    RiskIndicatorType,
    RiskLevel,
    Severity,
)
from app.models.intervention import Intervention
from app.models.milestone import StudentMilestone
from app.models.project import Project
from app.models.registration import Registration, RegistrationValidationLog
from app.models.result import CourseResult
from app.models.risk import RiskAssessment, RiskFactor, RiskRule
from app.models.student import Student
from app.services.cgpa_service import compute_cgpa
from app.services.notification_service import create_notification
from app.services.policy_service import get_policy
from app.models.enums import NotificationType

SEVERITY_BASE_POINTS = {Severity.info: 5.0, Severity.warning: 15.0, Severity.critical: 30.0}

RISK_LEVEL_ORDER = [RiskLevel.low, RiskLevel.moderate, RiskLevel.high, RiskLevel.critical]

RECOMMENDED_ACTIONS = {
    RiskIndicatorType.low_cgpa: "Schedule an academic counselling session to review study plan and course load.",
    RiskIndicatorType.failed_courses: "Recommend remedial support or a retake plan for the failed course(s).",
    RiskIndicatorType.insufficient_credits: "Review credit completion pace against program milestones with the student.",
    RiskIndicatorType.missed_milestone: "Follow up on the overdue milestone and agree a revised completion date.",
    RiskIndicatorType.pending_courses: "Check in on pending/incomplete course results and any blockers.",
    RiskIndicatorType.incomplete_project: "Contact the student about the overdue project and supervisor support.",
    RiskIndicatorType.registration_failures: "Walk the student through registration rules to avoid repeat rejections.",
    RiskIndicatorType.inactivity: "Reach out to confirm the student is still engaged with the program.",
    RiskIndicatorType.overdue_followup: "Complete the overdue intervention follow-up as soon as possible.",
}


def _indicator_observations(db: Session, student: Student) -> dict[RiskIndicatorType, dict]:
    """Compute the observed value for every indicator type. A value of None means
    the indicator could not be evaluated due to missing underlying data."""
    today = date.today()

    cgpa, completed_credits, _attempted = compute_cgpa(db, student.id)

    failed_courses = db.execute(
        select(CourseResult).where(
            CourseResult.student_id == student.id, CourseResult.result_status == ResultStatus.fail
        )
    ).scalars().all()

    milestones = db.execute(
        select(StudentMilestone).where(StudentMilestone.student_id == student.id)
    ).scalars().all()
    missed_milestones = [m for m in milestones if m.status == MilestoneStatus.overdue]

    pending_registrations = db.execute(
        select(Registration).where(
            Registration.student_id == student.id, Registration.status == RegistrationStatus.pending
        )
    ).scalars().all()
    incomplete_results = db.execute(
        select(CourseResult).where(
            CourseResult.student_id == student.id, CourseResult.result_status == ResultStatus.incomplete
        )
    ).scalars().all()

    projects = db.execute(select(Project).where(Project.student_id == student.id)).scalars().all()
    overdue_projects = [
        p for p in projects
        if p.due_date and p.due_date < today and p.status not in (ProjectStatus.completed, ProjectStatus.submitted)
    ]

    validation_logs = db.execute(
        select(RegistrationValidationLog).where(RegistrationValidationLog.student_id == student.id)
    ).scalars().all()
    failed_validations = [
        log for log in validation_logs if not log.validation_result.get("overall_valid", True)
    ]

    interventions = db.execute(
        select(Intervention).where(Intervention.student_id == student.id)
    ).scalars().all()
    overdue_followups = [
        i for i in interventions
        if i.follow_up_date and i.follow_up_date < today
        and i.status not in (InterventionStatus.completed, InterventionStatus.cancelled)
    ]

    last_activity_candidates: list[datetime] = []
    for r in db.execute(select(CourseResult).where(CourseResult.student_id == student.id)).scalars().all():
        last_activity_candidates.append(r.recorded_at)
    for reg in db.execute(select(Registration).where(Registration.student_id == student.id)).scalars().all():
        last_activity_candidates.append(reg.created_at)
    for interv in interventions:
        last_activity_candidates.append(interv.created_at)

    days_inactive = None
    if last_activity_candidates:
        most_recent = max(last_activity_candidates)
        if most_recent.tzinfo is None:
            most_recent = most_recent.replace(tzinfo=timezone.utc)
        days_inactive = (datetime.now(timezone.utc) - most_recent).days

    return {
        RiskIndicatorType.low_cgpa: {"value": cgpa, "available": cgpa is not None},
        RiskIndicatorType.failed_courses: {"value": len(failed_courses), "available": True},
        RiskIndicatorType.insufficient_credits: {"value": completed_credits, "available": True},
        RiskIndicatorType.missed_milestone: {"value": len(missed_milestones), "available": True},
        RiskIndicatorType.pending_courses: {
            "value": len(pending_registrations) + len(incomplete_results),
            "available": True,
        },
        RiskIndicatorType.incomplete_project: {"value": len(overdue_projects), "available": True},
        RiskIndicatorType.registration_failures: {"value": len(failed_validations), "available": True},
        RiskIndicatorType.inactivity: {"value": days_inactive, "available": days_inactive is not None},
        RiskIndicatorType.overdue_followup: {"value": len(overdue_followups), "available": True},
    }


def _evaluate_rule(rule: RiskRule, observed: dict) -> bool:
    value = observed["value"]
    if value is None:
        return False
    threshold = float(rule.threshold_value)
    if rule.indicator_type == RiskIndicatorType.low_cgpa:
        return float(value) < threshold
    if rule.indicator_type == RiskIndicatorType.insufficient_credits:
        return float(value) < threshold
    # All other indicators are "count/duration at or above threshold"
    return float(value) >= threshold


def _risk_level_for_score(db: Session, score: float) -> RiskLevel:
    thresholds = get_policy(db, "risk_level_thresholds")
    if score >= thresholds.get("critical", 75):
        return RiskLevel.critical
    if score >= thresholds.get("high", 50):
        return RiskLevel.high
    if score >= thresholds.get("moderate", 25):
        return RiskLevel.moderate
    return RiskLevel.low


def get_latest_assessment(db: Session, student_id: str) -> RiskAssessment | None:
    return db.execute(
        select(RiskAssessment)
        .where(RiskAssessment.student_id == student_id)
        .order_by(RiskAssessment.assessment_date.desc())
        .limit(1)
    ).scalar_one_or_none()


def assess_student_risk(db: Session, student: Student, *, notify_on_escalation: bool = True) -> RiskAssessment:
    """Evaluate a student against all active risk rules and persist a new,
    immutable RiskAssessment (previous assessments are never overwritten)."""
    rules = db.execute(
        select(RiskRule).where(
            RiskRule.is_active.is_(True),
            (RiskRule.academic_level.is_(None)) | (RiskRule.academic_level == student.academic_level),
        )
    ).scalars().all()

    observations = _indicator_observations(db, student)

    previous = get_latest_assessment(db, student.id)

    unavailable_indicators: list[str] = []

    # Collect every triggered rule first, then keep only the highest-scoring
    # rule PER INDICATOR TYPE. Admins may configure several severity tiers for
    # the same underlying indicator (e.g. "Low CGPA" warning vs "Critically
    # low CGPA" critical); counting every matching tier would double-count a
    # single underlying issue, so only the most severe triggered tier is kept.
    candidates: dict[RiskIndicatorType, dict] = {}

    for rule in rules:
        obs = observations.get(rule.indicator_type)
        if obs is None:
            continue
        if not obs["available"]:
            unavailable_indicators.append(rule.indicator_type.value)
            continue
        if _evaluate_rule(rule, obs):
            points = float(SEVERITY_BASE_POINTS[rule.severity]) * float(rule.weight)
            existing = candidates.get(rule.indicator_type)
            if existing is not None and existing["points_contributed"] >= points:
                continue
            candidates[rule.indicator_type] = {
                "rule_id": rule.id,
                "factor_name": rule.name,
                "observed_value": float(obs["value"]),
                "threshold_value": float(rule.threshold_value),
                "severity": rule.severity,
                "explanation": (
                    f"{rule.name}: observed value {obs['value']} crosses the configured "
                    f"threshold of {rule.threshold_value}."
                    if rule.indicator_type not in (RiskIndicatorType.low_cgpa, RiskIndicatorType.insufficient_credits)
                    else (
                        f"{rule.name}: observed value {obs['value']} is below the configured "
                        f"minimum of {rule.threshold_value}."
                    )
                ),
                "recommended_action": RECOMMENDED_ACTIONS.get(rule.indicator_type),
                "points_contributed": round(points, 2),
            }

    factor_rows = list(candidates.values())
    total_score = sum(row["points_contributed"] for row in factor_rows)

    risk_score = round(min(100.0, total_score), 2)
    risk_level = _risk_level_for_score(db, risk_score)

    data_note = None
    if unavailable_indicators:
        data_note = (
            "Some indicators could not be evaluated due to missing data ("
            + ", ".join(sorted(set(unavailable_indicators)))
            + "). This assessment reflects only the available evidence and should "
            "not be read as confirmation of low risk."
        )

    if factor_rows:
        summary = f"{len(factor_rows)} risk indicator(s) triggered; risk score {risk_score}/100 ({risk_level.value})."
    else:
        summary = "No configured risk indicators were triggered based on currently available data."

    assessment = RiskAssessment(
        student_id=student.id,
        risk_score=risk_score,
        risk_level=risk_level,
        summary=summary,
        data_completeness_note=data_note,
    )
    db.add(assessment)
    db.flush()

    for row in factor_rows:
        db.add(RiskFactor(assessment_id=assessment.id, **row))

    db.commit()
    db.refresh(assessment)

    if notify_on_escalation and previous is not None:
        _notify_if_escalated(db, student, previous, assessment)
    elif notify_on_escalation and previous is None and risk_level != RiskLevel.low:
        _notify_risk_level(db, student, assessment, is_new=True)

    return assessment


def _notify_if_escalated(db: Session, student: Student, previous: RiskAssessment, current: RiskAssessment) -> None:
    if RISK_LEVEL_ORDER.index(current.risk_level) > RISK_LEVEL_ORDER.index(previous.risk_level):
        _notify_risk_level(db, student, current, is_new=False)


def _notify_risk_level(db: Session, student: Student, assessment: RiskAssessment, *, is_new: bool) -> None:
    title = f"Risk level {'identified' if is_new else 'escalated'}: {assessment.risk_level.value.upper()}"
    message = (
        f"{student.full_name} ({student.student_identifier}) is now assessed as "
        f"{assessment.risk_level.value} risk (score {assessment.risk_score}/100). {assessment.summary}"
    )
    severity = Severity.critical if assessment.risk_level in (RiskLevel.high, RiskLevel.critical) else Severity.warning
    dedupe_key = f"risk_escalation:{student.id}:{assessment.id}"

    create_notification(
        db,
        user_id=student.user_id,
        student_id=student.id,
        notification_type=NotificationType.risk_escalation,
        title=title,
        message=message,
        severity=severity,
        dedupe_key=f"{dedupe_key}:student",
        send_email=True,
    )
    if student.assigned_staff_id:
        create_notification(
            db,
            user_id=student.assigned_staff_id,
            student_id=student.id,
            notification_type=NotificationType.risk_escalation,
            title=title,
            message=message,
            severity=severity,
            dedupe_key=f"{dedupe_key}:staff",
            send_email=True,
        )
