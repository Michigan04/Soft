from datetime import datetime

from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, new_uuid, utcnow


class StudentAssignment(Base):
    __tablename__ = "student_assignments"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(GUID, ForeignKey("students.id"), nullable=False, index=True)
    staff_user_id: Mapped[str] = mapped_column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    assigned_by: Mapped[str | None] = mapped_column(GUID, ForeignKey("users.id"), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    unassigned_at: Mapped[datetime | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    student = relationship("Student")
    staff_user = relationship("User", foreign_keys=[staff_user_id])
