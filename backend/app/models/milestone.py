from datetime import datetime

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, new_uuid
from app.models.enums import AcademicLevel, MilestoneStatus


class AcademicMilestone(Base):
    __tablename__ = "academic_milestones"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    academic_level: Mapped[AcademicLevel] = mapped_column(Enum(AcademicLevel, name="academic_level"), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_credits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_cgpa: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class StudentMilestone(Base):
    __tablename__ = "student_milestones"
    __table_args__ = (UniqueConstraint("student_id", "milestone_id", name="uq_student_milestone"),)

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(GUID, ForeignKey("students.id"), nullable=False, index=True)
    milestone_id: Mapped[str] = mapped_column(GUID, ForeignKey("academic_milestones.id"), nullable=False)
    status: Mapped[MilestoneStatus] = mapped_column(
        Enum(MilestoneStatus, name="milestone_status"), nullable=False, default=MilestoneStatus.not_started
    )
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    student = relationship("Student")
    milestone = relationship("AcademicMilestone")
