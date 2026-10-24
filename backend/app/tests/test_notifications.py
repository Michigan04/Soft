from app.models.enums import NotificationType, Severity
from app.services.notification_service import create_notification, notify_failed_result
from app.tests.conftest import make_student


def test_duplicate_notification_is_prevented_by_dedupe_key(db_session):
    _user, student = make_student(db_session, "notif1@test.dev", "NOTIF1")

    first = create_notification(
        db_session, user_id=student.user_id, student_id=student.id, notification_type=NotificationType.general,
        title="t", message="m", severity=Severity.info, dedupe_key="same-key",
    )
    second = create_notification(
        db_session, user_id=student.user_id, student_id=student.id, notification_type=NotificationType.general,
        title="t2", message="m2", severity=Severity.info, dedupe_key="same-key",
    )

    assert first is not None
    assert second is None  # duplicate suppressed


def test_different_dedupe_keys_both_created(db_session):
    _user, student = make_student(db_session, "notif2@test.dev", "NOTIF2")

    first = create_notification(
        db_session, user_id=student.user_id, student_id=student.id, notification_type=NotificationType.general,
        title="t", message="m", severity=Severity.info, dedupe_key="key-a",
    )
    second = create_notification(
        db_session, user_id=student.user_id, student_id=student.id, notification_type=NotificationType.general,
        title="t2", message="m2", severity=Severity.info, dedupe_key="key-b",
    )
    assert first is not None
    assert second is not None


def test_failure_alert_uses_console_backend_when_smtp_not_configured(db_session, seeded_courses, caplog):
    import logging

    _user, student = make_student(db_session, "notif3@test.dev", "NOTIF3")

    class FakeResult:
        id = "fake-result-id"
        student_id = student.id
        course_id = seeded_courses["course_a"].id

    with caplog.at_level(logging.INFO, logger="notifications"):
        notify_failed_result(db_session, FakeResult())
        db_session.commit()

    assert any("dev-email-backend" in message for message in caplog.messages)
