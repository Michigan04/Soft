from datetime import date, timedelta

from app.models.enums import InterventionOutcome, InterventionStatus, InterventionType, UserRole
from app.models.intervention import Intervention
from app.services.reporting_service import intervention_outcomes, overdue_followups_report, rows_to_csv
from app.tests.conftest import make_student, make_user


def test_intervention_outcomes_aggregation(db_session):
    staff = make_user(db_session, "repstaff@test.dev", UserRole.faculty)
    _user, student = make_student(db_session, "repstu@test.dev", "REP1")
    db_session.add_all([
        Intervention(student_id=student.id, staff_user_id=staff.id, intervention_type=InterventionType.call,
                     description="x", status=InterventionStatus.completed, outcome=InterventionOutcome.improved),
        Intervention(student_id=student.id, staff_user_id=staff.id, intervention_type=InterventionType.call,
                     description="y", status=InterventionStatus.completed, outcome=InterventionOutcome.improved),
        Intervention(student_id=student.id, staff_user_id=staff.id, intervention_type=InterventionType.call,
                     description="z", status=InterventionStatus.open, outcome=None),
    ])
    db_session.commit()

    rows = intervention_outcomes(db_session, None, None, None)
    counts = {r["outcome"]: r["count"] for r in rows}
    assert counts["improved"] == 2
    assert counts["pending"] == 1


def test_overdue_followups_report_excludes_completed(db_session):
    staff = make_user(db_session, "repstaff2@test.dev", UserRole.faculty)
    _user, student = make_student(db_session, "repstu2@test.dev", "REP2")
    db_session.add_all([
        Intervention(student_id=student.id, staff_user_id=staff.id, intervention_type=InterventionType.call,
                     description="overdue-open", status=InterventionStatus.open, follow_up_date=date.today() - timedelta(days=3)),
        Intervention(student_id=student.id, staff_user_id=staff.id, intervention_type=InterventionType.call,
                     description="overdue-completed", status=InterventionStatus.completed, follow_up_date=date.today() - timedelta(days=3)),
    ])
    db_session.commit()

    rows = overdue_followups_report(db_session)
    assert len(rows) == 1
    assert rows[0]["status"] == "open"


def test_rows_to_csv_handles_empty_and_populated():
    assert rows_to_csv([]) == ""
    csv_text = rows_to_csv([{"a": 1, "b": 2}])
    assert "a,b" in csv_text
    assert "1,2" in csv_text
