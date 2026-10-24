from datetime import date, datetime

from sqlalchemy import Date, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, TimestampMixin, new_uuid, utcnow
from app.models.enums import InterventionOutcome, InterventionStatus, InterventionType


class Intervention(TimestampMixin, Base):
    __tablename__ = "interventions"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(GUID, ForeignKey("students.id"), nullable=False, index=True)
    staff_user_id: Mapped[str] = mapped_column(GUID, ForeignKey("users.id"), nullable=False)
    intervention_type: Mapped[InterventionType] = mapped_column(
        Enum(InterventionType, name="intervention_type"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[InterventionStatus] = mapped_column(
        Enum(InterventionStatus, name="intervention_status"), nullable=False, default=InterventionStatus.open
    )
    outcome: Mapped[InterventionOutcome | None] = mapped_column(
        Enum(InterventionOutcome, name="intervention_outcome"), nullable=True
    )
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    student = relationship("Student")
    staff_user = relationship("User")
    history = relationship(
        "InterventionHistory", back_populates="intervention", order_by="InterventionHistory.changed_at"
    )


class InterventionHistory(Base):
    __tablename__ = "intervention_history"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    intervention_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("interventions.id"), nullable=False, index=True
    )
    changed_by: Mapped[str | None] = mapped_column(GUID, ForeignKey("users.id"), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    field_changed: Mapped[str] = mapped_column(Text, nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    intervention = relationship("Intervention", back_populates="history")
