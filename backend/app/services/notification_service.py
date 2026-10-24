import logging
import smtplib
from email.message import EmailMessage

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import utcnow
from app.models.enums import DeliveryChannel, DeliveryStatus, NotificationType, Severity
from app.models.notification import Notification, NotificationDelivery
from app.models.user import User

logger = logging.getLogger("notifications")


def _send_email(to_address: str, subject: str, body: str) -> tuple[DeliveryStatus, str | None]:
    """Send email via SMTP if configured, otherwise log to a console/dev backend.

    SMTP is optional (US-03): when SMTP_HOST is empty, the "console" backend simply
    logs the message so the app remains demoable without a live mail server.
    """
    if not settings.SMTP_HOST:
        logger.info("[dev-email-backend] To: %s | Subject: %s | Body: %s", to_address, subject, body)
        return DeliveryStatus.sent, None

    try:
        message = EmailMessage()
        message["From"] = settings.SMTP_FROM_ADDRESS
        message["To"] = to_address
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)
        return DeliveryStatus.sent, None
    except Exception as exc:  # pragma: no cover - network dependent
        logger.exception("Failed to send email to %s", to_address)
        return DeliveryStatus.failed, str(exc)


def create_notification(
    db: Session,
    *,
    user_id: str,
    student_id: str | None,
    notification_type: NotificationType,
    title: str,
    message: str,
    severity: Severity = Severity.info,
    dedupe_key: str | None = None,
    send_email: bool = False,
    commit: bool = True,
) -> Notification | None:
    """Create an in-app notification, optionally emailing it. Returns None if a
    notification with the same dedupe_key already exists (prevents duplicate alerts)."""
    if dedupe_key:
        existing = db.execute(
            select(Notification).where(Notification.dedupe_key == dedupe_key)
        ).scalar_one_or_none()
        if existing is not None:
            return None

    notification = Notification(
        user_id=user_id,
        student_id=student_id,
        notification_type=notification_type,
        title=title,
        message=message,
        severity=severity,
        dedupe_key=dedupe_key,
    )
    db.add(notification)
    db.flush()

    in_app_delivery = NotificationDelivery(
        notification_id=notification.id,
        channel=DeliveryChannel.in_app,
        delivery_status=DeliveryStatus.sent,
        attempt_count=1,
        sent_at=utcnow(),
    )
    db.add(in_app_delivery)

    if send_email:
        user = db.get(User, user_id)
        if user is not None:
            status_result, error = _send_email(user.email, title, message)
            email_delivery = NotificationDelivery(
                notification_id=notification.id,
                channel=DeliveryChannel.email,
                delivery_status=status_result,
                attempt_count=1,
                error_message=error,
                sent_at=utcnow() if status_result == DeliveryStatus.sent else None,
            )
            db.add(email_delivery)

    if commit:
        db.commit()
        db.refresh(notification)
    return notification


def notify_failed_result(db: Session, course_result) -> None:
    """Generate a deduplicated failure alert for a newly recorded failed result (US-03)."""
    from app.models.academic import Course
    from app.models.student import Student

    student = db.get(Student, course_result.student_id)
    course = db.get(Course, course_result.course_id)
    if student is None or course is None:
        return

    title = f"Failed result recorded: {course.course_code}"
    message = (
        f"{student.full_name} ({student.student_identifier}) has a recorded FAIL in "
        f"{course.course_code} - {course.course_name}. Suggested next step: review remedial "
        f"options and consider an academic counselling follow-up."
    )
    dedupe_base = f"failure_alert:{course_result.id}"

    create_notification(
        db,
        user_id=student.user_id,
        student_id=student.id,
        notification_type=NotificationType.failure_alert,
        title=title,
        message=message,
        severity=Severity.warning,
        dedupe_key=f"{dedupe_base}:student",
        send_email=True,
        commit=False,
    )
    if student.assigned_staff_id:
        create_notification(
            db,
            user_id=student.assigned_staff_id,
            student_id=student.id,
            notification_type=NotificationType.failure_alert,
            title=title,
            message=message,
            severity=Severity.warning,
            dedupe_key=f"{dedupe_base}:staff",
            send_email=True,
            commit=False,
        )
