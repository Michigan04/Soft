from app.models.enums import (
    AcademicLevel,
    NotificationType,
    ResultStatus,
    RiskIndicatorType,
    RiskLevel,
    Severity,
)
from app.models.result import CourseResult
from app.models.risk import RiskRule
from app.services.risk_engine import assess_student_risk, get_latest_assessment
from app.tests.conftest import make_student


def _add_rule(db_session, indicator_type, threshold, severity=Severity.warning, weight=1.0):
    rule = RiskRule(name=f"rule-{indicator_type.value}", indicator_type=indicator_type, threshold_value=threshold, severity=severity, weight=weight)
    db_session.add(rule)
    db_session.commit()
    return rule


def test_no_data_does_not_classify_as_safe_silently(client, db_session, default_policies):
    """A student with zero academic records must not be silently marked low-risk
    without explanation; missing indicators must be flagged explicitly."""
    _user, student = make_student(db_session, "nodata@test.dev", "NODATA1")
    _add_rule(db_session, RiskIndicatorType.low_cgpa, 5.0)
    _add_rule(db_session, RiskIndicatorType.insufficient_credits, 4)

    assessment = assess_student_risk(db_session, student, notify_on_escalation=False)

    assert assessment.data_completeness_note is not None
    assert "low_cgpa" in assessment.data_completeness_note
    # insufficient_credits IS evaluable (0 credits) and should trigger
    assert any(f.factor_name.startswith("rule-insufficient_credits") for f in assessment.factors)


def test_failed_course_triggers_risk_factor_with_explanation(client, db_session, seeded_courses, default_policies):
    _user, student = make_student(db_session, "fail@test.dev", "FAIL1", academic_level=AcademicLevel.foundation)
    _add_rule(db_session, RiskIndicatorType.failed_courses, 1)

    db_session.add(CourseResult(
        student_id=student.id, course_id=seeded_courses["course_a"].id, academic_term_id=seeded_courses["term"].id,
        grade="F", grade_points=2, credits=4, result_status=ResultStatus.fail,
    ))
    db_session.commit()

    assessment = assess_student_risk(db_session, student, notify_on_escalation=False)
    assert assessment.risk_score > 0
    assert len(assessment.factors) == 1
    assert "crosses the configured threshold" in assessment.factors[0].explanation


def test_overlapping_severity_tiers_do_not_double_count(client, db_session, seeded_courses, default_policies):
    """Two rules on the same indicator type (different severities) must not both
    contribute points for the same underlying issue."""
    _user, student = make_student(db_session, "dupe@test.dev", "DUPE1")
    _add_rule(db_session, RiskIndicatorType.low_cgpa, 5.0, severity=Severity.warning, weight=1.0)
    _add_rule(db_session, RiskIndicatorType.low_cgpa, 4.0, severity=Severity.critical, weight=1.0)

    db_session.add(CourseResult(
        student_id=student.id, course_id=seeded_courses["course_a"].id, academic_term_id=seeded_courses["term"].id,
        grade="F", grade_points=2, credits=4, result_status=ResultStatus.pass_,
    ))
    db_session.commit()

    assessment = assess_student_risk(db_session, student, notify_on_escalation=False)
    low_cgpa_factors = [f for f in assessment.factors if "low_cgpa" in f.factor_name]
    assert len(low_cgpa_factors) == 1
    assert low_cgpa_factors[0].severity == Severity.critical  # keeps the more severe tier only


def test_risk_assessment_history_is_preserved_not_overwritten(client, db_session, default_policies):
    _user, student = make_student(db_session, "hist@test.dev", "HIST1")
    _add_rule(db_session, RiskIndicatorType.insufficient_credits, 4)

    first = assess_student_risk(db_session, student, notify_on_escalation=False)
    second = assess_student_risk(db_session, student, notify_on_escalation=False)

    assert first.id != second.id
    latest = get_latest_assessment(db_session, student.id)
    assert latest.id == second.id

    from sqlalchemy import select
    from app.models.risk import RiskAssessment
    all_assessments = db_session.execute(select(RiskAssessment).where(RiskAssessment.student_id == student.id)).scalars().all()
    assert len(all_assessments) == 2


def test_risk_escalation_sends_notification(client, db_session, seeded_courses, default_policies):
    _user, student = make_student(db_session, "esc@test.dev", "ESC1")
    _add_rule(db_session, RiskIndicatorType.failed_courses, 1, severity=Severity.critical, weight=3.0)

    assess_student_risk(db_session, student)  # first pass: low (no data yet)

    db_session.add(CourseResult(
        student_id=student.id, course_id=seeded_courses["course_a"].id, academic_term_id=seeded_courses["term"].id,
        grade="F", grade_points=2, credits=4, result_status=ResultStatus.fail,
    ))
    db_session.commit()

    assess_student_risk(db_session, student)  # second pass: should escalate

    from sqlalchemy import select
    from app.models.notification import Notification
    notifications = db_session.execute(
        select(Notification).where(
            Notification.student_id == student.id, Notification.notification_type == NotificationType.risk_escalation
        )
    ).scalars().all()
    assert len(notifications) >= 1
