from app.models.enums import UserRole
from app.tests.conftest import login, make_student, make_user


def test_login_success_and_me(client, db_session):
    make_user(db_session, "admin@test.dev", UserRole.admin, password="Secret123!")
    headers = login(client, "admin@test.dev", "Secret123!")
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "admin@test.dev"
    assert body["role"] == "admin"


def test_login_wrong_password_rejected(client, db_session):
    make_user(db_session, "user@test.dev", UserRole.student, password="Secret123!")
    resp = client.post("/api/v1/auth/login", data={"username": "user@test.dev", "password": "wrong"})
    assert resp.status_code == 401


def test_unauthenticated_request_rejected(client):
    resp = client.get("/api/v1/students")
    assert resp.status_code == 401


def test_role_based_authorization_rejects_student_listing(client, db_session):
    _user, _student = make_student(db_session, "stu@test.dev", "ID001")
    headers = login(client, "stu@test.dev")
    resp = client.get("/api/v1/students", headers=headers)
    assert resp.status_code == 403


def test_admin_can_list_students(client, db_session):
    make_user(db_session, "admin2@test.dev", UserRole.admin, password="Secret123!")
    make_student(db_session, "stu2@test.dev", "ID002")
    headers = login(client, "admin2@test.dev", "Secret123!")
    resp = client.get("/api/v1/students", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
