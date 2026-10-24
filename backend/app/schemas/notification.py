from datetime import datetime

from pydantic import BaseModel

from app.models.enums import NotificationType, Severity


class NotificationOut(BaseModel):
    id: str
    student_id: str | None
    notification_type: NotificationType
    title: str
    message: str
    severity: Severity
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
