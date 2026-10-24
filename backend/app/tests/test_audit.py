from app.models.enums import UserRole
from app.services.audit_service import record_audit_event
from app.tests.conftest import login, make_student, make_user


def test_audit_event_recorded_with_before_after(db_session):
    admin = make_user(db_session, "auditadmin@test.dev", UserRole.admin)
    entry = record_audit_event(
        db_session, actor_user_id=admin.id, action="update", entity_type="student", entity_id="abc",
        before_data={"status": "active"}, after_data={"status": "on_hold"},
    )
    assert entry.id is not None
    assert entry.before_data == {"status": "active"}
    assert entry.after_data == {"status": "on_hold"}


def test_only_admin_can_list_audit_logs(client, db_session):
    make_user(db_session, "regularstaff@test.dev", UserRole.faculty, password="Secret123!")
    headers = login(client, "regularstaff@test.dev", "Secret123!")
    resp = client.get("/api/v1/audit-logs", headers=headers)
    assert resp.status_code == 403


def test_admin_can_list_audit_logs(client, db_session):
    admin = make_user(db_session, "auditadmin2@test.dev", UserRole.admin, password="Secret123!")
    record_audit_event(db_session, actor_user_id=admin.id, action="create", entity_type="student", entity_id="xyz", after_data={"a": 1})
    headers = login(client, "auditadmin2@test.dev", "Secret123!")
    resp = client.get("/api/v1/audit-logs", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_no_endpoint_allows_deleting_audit_logs(client, db_session):
    admin = make_user(db_session, "auditadmin3@test.dev", UserRole.admin, password="Secret123!")
    headers = login(client, "auditadmin3@test.dev", "Secret123!")
    resp = client.delete("/api/v1/audit-logs", headers=headers)
    assert resp.status_code == 405  # method not allowed; no delete route exists
