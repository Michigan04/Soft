from app.models.enums import UserRole
from app.tests.conftest import login, make_student, make_user


def test_student_cannot_access_other_students_profile(client, db_session):
    _user_a, student_a = make_student(db_session, "a@test.dev", "IDA1")
    _user_b, student_b = make_student(db_session, "b@test.dev", "IDB1")
    headers = login(client, "a@test.dev")

    own = client.get(f"/api/v1/students/{student_a.id}", headers=headers)
    assert own.status_code == 200

    other = client.get(f"/api/v1/students/{student_b.id}", headers=headers)
    assert other.status_code == 403


def test_staff_cannot_access_unassigned_student(client, db_session):
    staff = make_user(db_session, "faculty@test.dev", UserRole.faculty, password="Secret123!")
    _user, student = make_student(db_session, "c@test.dev", "IDC1")  # not assigned to staff
    headers = login(client, "faculty@test.dev", "Secret123!")

    resp = client.get(f"/api/v1/students/{student.id}", headers=headers)
    assert resp.status_code == 403


def test_staff_can_access_assigned_student(client, db_session):
    staff = make_user(db_session, "faculty2@test.dev", UserRole.faculty, password="Secret123!")
    _user, student = make_student(db_session, "d@test.dev", "IDD1", assigned_staff_id=staff.id)
    headers = login(client, "faculty2@test.dev", "Secret123!")

    resp = client.get(f"/api/v1/students/{student.id}", headers=headers)
    assert resp.status_code == 200


def test_cannot_access_other_student_by_guessing_id(client, db_session):
    """A student changing the URL/ID in the request must not reveal another student's data."""
    _user_a, student_a = make_student(db_session, "e@test.dev", "IDE1")
    _user_b, student_b = make_student(db_session, "f@test.dev", "IDF1")
    headers = login(client, "e@test.dev")

    resp = client.get(f"/api/v1/students/{student_b.id}/risk-assessments", headers=headers)
    assert resp.status_code == 403
