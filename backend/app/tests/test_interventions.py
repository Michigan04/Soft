from datetime import date, timedelta

from app.models.enums import InterventionStatus, InterventionType, UserRole
from app.schemas.intervention import InterventionCreate, InterventionUpdate
from app.services.intervention_service import create_intervention, is_overdue, update_intervention
from app.tests.conftest import make_student, make_user


def test_create_intervention_records_history(db_session):
    staff = make_user(db_session, "staff1@test.dev", UserRole.faculty)
    _user, student = make_student(db_session, "ivstu1@test.dev", "IV1")

    data = InterventionCreate(student_id=student.id, intervention_type=InterventionType.call, description="Checked in.")
    intervention = create_intervention(db_session, data, staff.id)

    assert intervention.status == InterventionStatus.open
    assert len(intervention.history) == 1
    assert intervention.history[0].field_changed == "created"


def test_update_intervention_tracks_outcome_and_history(db_session):
    staff = make_user(db_session, "staff2@test.dev", UserRole.faculty)
    _user, student = make_student(db_session, "ivstu2@test.dev", "IV2")
    data = InterventionCreate(student_id=student.id, intervention_type=InterventionType.meeting, description="Met with student.")
    intervention = create_intervention(db_session, data, staff.id)

    update = InterventionUpdate(status=InterventionStatus.completed, outcome="improved")
    updated = update_intervention(db_session, intervention, update, staff.id)

    assert updated.status == InterventionStatus.completed
    assert updated.outcome.value == "improved"
    assert updated.completed_at is not None
    field_names = {h.field_changed for h in updated.history}
    assert "status" in field_names
    assert "outcome" in field_names


def test_overdue_followup_detection(db_session):
    staff = make_user(db_session, "staff3@test.dev", UserRole.faculty)
    _user, student = make_student(db_session, "ivstu3@test.dev", "IV3")

    overdue_data = InterventionCreate(
        student_id=student.id, intervention_type=InterventionType.call, description="x",
        follow_up_date=date.today() - timedelta(days=5),
    )
    upcoming_data = InterventionCreate(
        student_id=student.id, intervention_type=InterventionType.call, description="y",
        follow_up_date=date.today() + timedelta(days=5),
    )
    overdue = create_intervention(db_session, overdue_data, staff.id)
    upcoming = create_intervention(db_session, upcoming_data, staff.id)

    assert is_overdue(overdue) is True
    assert is_overdue(upcoming) is False


def test_completed_intervention_is_never_overdue(db_session):
    staff = make_user(db_session, "staff4@test.dev", UserRole.faculty)
    _user, student = make_student(db_session, "ivstu4@test.dev", "IV4")
    data = InterventionCreate(
        student_id=student.id, intervention_type=InterventionType.call, description="x",
        follow_up_date=date.today() - timedelta(days=5),
    )
    intervention = create_intervention(db_session, data, staff.id)
    update_intervention(db_session, intervention, InterventionUpdate(status=InterventionStatus.completed), staff.id)

    assert is_overdue(intervention) is False
