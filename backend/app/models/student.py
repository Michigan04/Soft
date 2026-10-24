from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, TimestampMixin, new_uuid
from app.models.enums import AcademicLevel, ProgramStatus


class Student(TimestampMixin, Base):
    __tablename__ = "students"
    __table_args__ = (
        Index("ix_students_academic_level", "academic_level"),
        Index("ix_students_assigned_staff", "assigned_staff_id"),
    )

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    student_identifier: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(GUID, ForeignKey("users.id"), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    academic_level: Mapped[AcademicLevel] = mapped_column(Enum(AcademicLevel, name="academic_level"), nullable=False)
    program_status: Mapped[ProgramStatus] = mapped_column(
        Enum(ProgramStatus, name="program_status"), nullable=False, default=ProgramStatus.active
    )
    admission_date: Mapped[date] = mapped_column(Date, nullable=False)
    current_term: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assigned_staff_id: Mapped[str | None] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=True
    )

    user = relationship("User", back_populates="student_profile", foreign_keys=[user_id])
    assigned_staff = relationship("User", foreign_keys=[assigned_staff_id])
