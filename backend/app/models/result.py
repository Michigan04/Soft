from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, new_uuid, utcnow
from app.models.enums import ResultStatus


class CourseResult(Base):
    __tablename__ = "course_results"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", "academic_term_id", name="uq_result_student_course_term"),
    )

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(GUID, ForeignKey("students.id"), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(GUID, ForeignKey("courses.id"), nullable=False)
    academic_term_id: Mapped[str] = mapped_column(GUID, ForeignKey("academic_terms.id"), nullable=False)
    grade: Mapped[str | None] = mapped_column(String(4), nullable=True)
    grade_points: Mapped[float | None] = mapped_column(Numeric(3, 1), nullable=True)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    result_status: Mapped[ResultStatus] = mapped_column(Enum(ResultStatus, name="result_status"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    student = relationship("Student")
    course = relationship("Course")
    academic_term = relationship("AcademicTerm")
