from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, new_uuid, utcnow
from app.models.enums import DeliveryChannel, DeliveryStatus, NotificationType, Severity


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    student_id: Mapped[str | None] = mapped_column(GUID, ForeignKey("students.id"), nullable=True)
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[Severity] = mapped_column(Enum(Severity, name="severity"), nullable=False, default=Severity.info)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    deliveries = relationship("NotificationDelivery", back_populates="notification")


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    notification_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("notifications.id"), nullable=False, index=True
    )
    channel: Mapped[DeliveryChannel] = mapped_column(Enum(DeliveryChannel, name="delivery_channel"), nullable=False)
    delivery_status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status"), nullable=False, default=DeliveryStatus.pending
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    notification = relationship("Notification", back_populates="deliveries")
